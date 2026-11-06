"""Leo desktop UI.

The UI deliberately stays on Tkinter: it is available with the supported
Windows Python installation, keeps packaging simple, and does not replace the
assistant backend. Model calls, microphone capture, and speech synthesis are
always dispatched off the Tk event loop.
"""

from __future__ import annotations

import math
import queue
import threading
import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Any, Callable

from core.config import settings
from core.memory import (
    clear_conversation,
    delete_fact,
    get_all_facts,
    load_recent_history,
    save_fact,
)

BG = "#0D0E14"
SIDEBAR = "#12141D"
PANEL = "#171A25"
PANEL_ALT = "#1D2130"
TEXT = "#F5F7FF"
MUTED = "#8E96AA"
ACCENT = "#8B5CF6"
ACCENT_BLUE = "#38BDF8"
SUCCESS = "#34D399"
WARNING = "#FBBF24"
ERROR = "#FB7185"

COLORS = {
    "listening": ACCENT_BLUE,
    "transcribing": "#A78BFA",
    "thinking": ACCENT,
    "speaking": SUCCESS,
    "idle": "#64748B",
    "error": ERROR,
}
LABELS = {
    "listening": "Listening",
    "transcribing": "Transcribing",
    "thinking": "Thinking",
    "speaking": "Speaking",
    "idle": "Ready",
    "error": "Error",
}

_state_queue: queue.Queue[tuple[str, str]] = queue.Queue()


@dataclass(frozen=True)
class UiEvent:
    kind: str
    value: Any = None


def set_state(state: str, text: str = "") -> None:
    """Publish a state update for the compatibility floating window."""
    _state_queue.put((state, text))


def _rounded_frame(parent: tk.Misc, **kwargs: Any) -> tk.Frame:
    """Return a themed frame; Tkinter's frame is intentionally borderless."""
    return tk.Frame(parent, bg=kwargs.pop("bg", PANEL), **kwargs)


class LeoDesktopApp:
    """Responsive main window connected to the real Leo services."""

    def __init__(
        self,
        root: tk.Tk,
        *,
        graph_factory: Callable[[], Any] | None = None,
        voice_listen: Callable[..., str] | None = None,
        voice_speak: Callable[[str], None] | None = None,
    ) -> None:
        self.root = root
        self.graph_factory = graph_factory
        self.voice_listen = voice_listen
        self.voice_speak = voice_speak
        self.events: queue.Queue[UiEvent] = queue.Queue()
        self.stop_event = threading.Event()
        self.worker: threading.Thread | None = None
        self.graph: Any = None
        self._poll_after_id: str | None = None
        self._orb_after_id: str | None = None
        self.history: list[dict[str, str]] = load_recent_history()
        self.state = "idle"
        self._build_window()
        self._poll_events()
        self._render_history()

    def _build_window(self) -> None:
        self.root.title("Leo · Personal AI")
        self.root.geometry("1120x720")
        self.root.minsize(880, 600)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("Leo.TButton", background=PANEL_ALT, foreground=TEXT,
                        borderwidth=0, padding=(12, 8), font=("Segoe UI", 10))
        style.map("Leo.TButton", background=[("active", "#2B3043")])
        style.configure("Leo.TEntry", fieldbackground=PANEL_ALT, foreground=TEXT,
                        insertcolor=TEXT, borderwidth=0)

        self.sidebar = tk.Frame(self.root, bg=SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)
        self._build_sidebar()
        self._build_header()
        self._build_chat()
        self._build_status_bar()

    def _build_sidebar(self) -> None:
        brand = tk.Frame(self.sidebar, bg=SIDEBAR)
        brand.pack(fill="x", padx=22, pady=(24, 28))
        tk.Label(brand, text="✦", fg=ACCENT_BLUE, bg=SIDEBAR,
                 font=("Segoe UI", 26, "bold")).pack(side="left")
        tk.Label(brand, text="LEO", fg=TEXT, bg=SIDEBAR,
                 font=("Segoe UI", 16, "bold")).pack(side="left", padx=9)
        tk.Label(self.sidebar, text="PERSONAL AI", fg=MUTED, bg=SIDEBAR,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=24, pady=(0, 10))
        self._nav_button("＋  New conversation", self.new_conversation)
        self._nav_button("◌  Memories", self.show_memories)
        self._nav_button("◒  Activity", self.show_activity)
        self._nav_button("⚙  Settings", self.show_settings)
        tk.Frame(self.sidebar, bg=SIDEBAR).pack(fill="both", expand=True)
        tk.Label(self.sidebar, text="LOCAL FIRST", fg=SUCCESS, bg=SIDEBAR,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=24)
        tk.Label(self.sidebar, text=f"{settings.model} · Ollama", fg=MUTED, bg=SIDEBAR,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=24, pady=(3, 22))

    def _nav_button(self, text: str, command: Callable[[], None]) -> None:
        button = tk.Button(
            self.sidebar, text=text, command=command, anchor="w",
            bg=SIDEBAR, fg=MUTED, activebackground=PANEL_ALT,
            activeforeground=TEXT, relief="flat", borderwidth=0,
            padx=24, pady=10, font=("Segoe UI", 10), cursor="hand2",
        )
        button.pack(fill="x")

    def _build_header(self) -> None:
        header = tk.Frame(self.content, bg=BG, height=72)
        header.pack(fill="x", padx=30, pady=(18, 0))
        header.pack_propagate(False)
        self.page_title = tk.Label(header, text="New conversation", bg=BG, fg=TEXT,
                                   font=("Segoe UI", 20, "bold"))
        self.page_title.pack(side="left", anchor="center")
        self.model_badge = tk.Label(
            header, text=f"●  Local · {settings.model}", bg=BG, fg=SUCCESS,
            font=("Segoe UI", 9),
        )
        self.model_badge.pack(side="right", anchor="center")

    def _build_chat(self) -> None:
        self.main = tk.Frame(self.content, bg=BG)
        self.main.pack(fill="both", expand=True, padx=30)
        self.orb = tk.Canvas(self.main, width=150, height=150, bg=BG,
                             highlightthickness=0)
        self.orb.pack(pady=(8, 2))
        self._draw_orb()
        self.status_label = tk.Label(self.main, text="Ready when you are",
                                     bg=BG, fg=MUTED, font=("Segoe UI", 11))
        self.status_label.pack()

        history_frame = _rounded_frame(self.main, bg=PANEL)
        history_frame.pack(fill="both", expand=True, pady=(18, 14))
        self.chat = tk.Text(
            history_frame, bg=PANEL, fg=TEXT, insertbackground=TEXT,
            relief="flat", borderwidth=0, wrap="word", state="disabled",
            padx=22, pady=16, font=("Segoe UI", 10),
        )
        self.chat.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(history_frame, command=self.chat.yview)
        scroll.pack(side="right", fill="y")
        self.chat.configure(yscrollcommand=scroll.set)
        self.chat.tag_configure("user", foreground=ACCENT_BLUE, spacing1=10)
        self.chat.tag_configure("assistant", foreground=TEXT, spacing1=10)
        self.chat.tag_configure("meta", foreground=MUTED, font=("Segoe UI", 8))

        composer = tk.Frame(self.main, bg=BG)
        composer.pack(fill="x", pady=(0, 18))
        self.input = tk.Text(composer, height=3, bg=PANEL_ALT, fg=TEXT,
                             insertbackground=TEXT, relief="flat", wrap="word",
                             padx=14, pady=10, font=("Segoe UI", 10))
        self.input.pack(side="left", fill="both", expand=True)
        self.input.bind("<Return>", self._on_return)
        self.input.bind("<Shift-Return>", lambda _: None)
        ttk.Button(composer, text="Send  ↵", style="Leo.TButton",
                   command=self.submit_text).pack(side="left", padx=(10, 0), fill="y")
        ttk.Button(composer, text="●", style="Leo.TButton",
                   command=self.start_voice).pack(side="left", padx=(8, 0), fill="y")

    def _build_status_bar(self) -> None:
        self.status_bar = tk.Frame(self.content, bg=SIDEBAR, height=30)
        self.status_bar.pack(fill="x", side="bottom")
        self.status_bar.pack_propagate(False)
        self.status_detail = tk.Label(
            self.status_bar, text="  ●  Microphone available  ·  SQLite memory active",
            bg=SIDEBAR, fg=MUTED, anchor="w", font=("Segoe UI", 8),
        )
        self.status_detail.pack(fill="both", padx=8)

    def _draw_orb(self) -> None:
        if self._orb_after_id is not None:
            try:
                self.root.after_cancel(self._orb_after_id)
            except tk.TclError:
                pass
            self._orb_after_id = None
        self.orb.delete("all")
        color = COLORS.get(self.state, COLORS["idle"])
        self.orb.create_oval(25, 25, 125, 125, fill="#161A2A", outline="")
        self.orb.create_oval(38, 38, 112, 112, fill=color, outline="")
        self.orb.create_oval(55, 55, 95, 95, fill="#F8FAFC", outline="")
        self.orb.create_oval(66, 66, 84, 84, fill=color, outline="")
        if self.state != "idle" and not self.stop_event.is_set():
            self._orb_after_id = self.root.after(70, self._animate_orb)

    def _animate_orb(self) -> None:
        self._orb_after_id = None
        if not self.stop_event.is_set() and self.root.winfo_exists():
            self._draw_orb()

    def _on_return(self, event: tk.Event) -> str:
        if event.state & 0x0001:
            return ""
        self.submit_text()
        return "break"

    def _render_history(self) -> None:
        self.chat.configure(state="normal")
        self.chat.delete("1.0", "end")
        for message in self.history:
            role = message["role"]
            if role not in {"user", "assistant"}:
                continue
            name = "You" if role == "user" else "Leo"
            timestamp = datetime.now().strftime("%H:%M")
            self.chat.insert("end", f"{name}  {timestamp}\n", "meta")
            self.chat.insert("end", f"{message['content']}\n\n", role)
        self.chat.configure(state="disabled")
        self.chat.see("end")

    def _set_state(self, state: str, detail: str = "") -> None:
        self.state = state
        self.status_label.configure(
            text=detail or LABELS.get(state, "Ready"),
            fg=COLORS.get(state, MUTED),
        )
        self._draw_orb()

    def _poll_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event.kind == "state":
                    state, detail = event.value
                    self._set_state(state, detail)
                elif event.kind == "message":
                    self.history.append(event.value)
                    self._render_history()
                elif event.kind == "error":
                    self._set_state("error", str(event.value))
                    messagebox.showerror("Leo", str(event.value), parent=self.root)
                elif event.kind == "ready":
                    self._set_state("idle", "Ready when you are")
        except queue.Empty:
            pass
        if not self.stop_event.is_set():
            self._poll_after_id = self.root.after(80, self._poll_events)

    def _run_worker(self, task: Callable[[], None]) -> None:
        if self.worker and self.worker.is_alive():
            return
        self.worker = threading.Thread(target=task, daemon=True)
        self.worker.start()

    def _get_graph(self) -> Any:
        if self.graph is None:
            from core.agent import build_leo
            self.graph = (self.graph_factory or build_leo)()
        return self.graph

    def submit_text(self) -> None:
        text = self.input.get("1.0", "end").strip()
        if not text:
            return
        self.input.delete("1.0", "end")
        self._run_worker(lambda: self._respond(text))

    def _respond(self, text: str) -> None:
        from core.agent import (
            clean_response,
            is_greeting,
            record_diagnostic,
            try_handle_remember,
        )
        from core.memory import save_message

        self.events.put(UiEvent("message", {"role": "user", "content": text}))
        save_message("user", text)
        self.events.put(UiEvent("state", ("thinking", "Thinking…")))
        try:
            reply = "Hey! How can I help you today?" if is_greeting(text) else try_handle_remember(text)
            if not reply:
                result = self._get_graph().invoke({
                    "messages": self.history + [{"role": "user", "content": text}]
                })
                reply = clean_response(result["messages"][-1].content)
            save_message("assistant", reply)
            self.events.put(UiEvent("message", {"role": "assistant", "content": reply}))
            self.events.put(UiEvent("state", ("speaking", reply)))
            if self.voice_speak:
                self.voice_speak(reply)
        except Exception as exc:
            record_diagnostic("desktop UI response", exc)
            self.events.put(UiEvent("error", f"Leo could not respond: {exc}"))
        finally:
            self.events.put(UiEvent("ready"))

    def start_voice(self) -> None:
        if self.voice_listen is None:
            from core.voice import listen
            self.voice_listen = listen
        self._run_worker(self._voice_task)

    def _voice_task(self) -> None:
        self.events.put(UiEvent("state", ("listening", "Listening…")))
        try:
            if self.voice_speak is None:
                from core.voice import speak
                self.voice_speak = speak
            text = self.voice_listen(
                duration=4,
                on_transcribing=lambda: self.events.put(
                    UiEvent("state", ("transcribing", "Transcribing…"))
                ),
            )
            if text:
                self.events.put(UiEvent("state", ("thinking", text)))
                self._respond(text)
            else:
                self.events.put(UiEvent("ready"))
        except Exception as exc:
            self.events.put(UiEvent("error", f"Voice input failed: {exc}"))

    def new_conversation(self) -> None:
        if messagebox.askyesno("New conversation", "Clear the current conversation history?",
                               parent=self.root):
            clear_conversation()
            self.history.clear()
            self._render_history()
            self.page_title.configure(text="New conversation")

    def show_memories(self) -> None:
        facts = get_all_facts()
        dialog = tk.Toplevel(self.root)
        dialog.title("Leo memories")
        dialog.configure(bg=BG)
        dialog.geometry("520x420")
        tk.Label(dialog, text="Memories", bg=BG, fg=TEXT,
                 font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=24, pady=20)
        listbox = tk.Listbox(dialog, bg=PANEL, fg=TEXT, relief="flat",
                             selectbackground=ACCENT, height=12)
        listbox.pack(fill="both", expand=True, padx=24)
        for fact in facts:
            listbox.insert("end", fact)
        controls = tk.Frame(dialog, bg=BG)
        controls.pack(fill="x", padx=24, pady=18)
        entry = tk.Entry(controls, bg=PANEL_ALT, fg=TEXT, insertbackground=TEXT, relief="flat")
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        def add() -> None:
            if entry.get().strip():
                save_fact(entry.get())
                entry.delete(0, "end")
                listbox.insert("end", get_all_facts()[0])
        def remove() -> None:
            selection = listbox.curselection()
            if selection and messagebox.askyesno("Delete memory", "Forget this memory?", parent=dialog):
                delete_fact(listbox.get(selection[0]))
                listbox.delete(selection[0])
        ttk.Button(controls, text="Add", command=add).pack(side="left", padx=8)
        ttk.Button(controls, text="Delete", command=remove).pack(side="left")

    def show_activity(self) -> None:
        self.page_title.configure(text="Activity")
        self._set_state("idle", "Local model and memory ready")

    def show_settings(self) -> None:
        self.page_title.configure(text="Settings")
        messagebox.showinfo(
            "Leo settings",
            f"Model: {settings.model}\nOllama: {settings.ollama_url}\n"
            f"TTS: {settings.tts_provider}\nDatabase: {settings.db_path}",
            parent=self.root,
        )

    def shutdown(self) -> None:
        self.stop_event.set()
        for after_id in (self._poll_after_id, self._orb_after_id):
            if after_id is not None:
                try:
                    self.root.after_cancel(after_id)
                except tk.TclError:
                    pass
        self._poll_after_id = None
        self._orb_after_id = None
        self.root.destroy()


def run_desktop_app() -> None:
    """Launch the full desktop app."""
    # Import the backend before starting worker threads so the first chat
    # request does not pay the dependency-import cost on the UI worker.
    from core import agent  # noqa: F401

    root = tk.Tk()
    LeoDesktopApp(root)
    root.mainloop()


def _run_floating_ui() -> None:
    """Compatibility popup used by the terminal voice loop."""
    root = tk.Tk()
    root.title("Leo")
    root.geometry("360x130+{}+30".format((root.winfo_screenwidth() - 360) // 2))
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.configure(bg=BG)
    canvas = tk.Canvas(root, width=360, height=130, bg=BG, highlightthickness=0)
    canvas.pack()
    circle = canvas.create_oval(28, 38, 78, 88, fill=COLORS["idle"], outline="")
    label = canvas.create_text(100, 50, text="Leo", fill=TEXT,
                               font=("Segoe UI", 15, "bold"), anchor="w")
    sub = canvas.create_text(100, 76, text="", fill=MUTED, font=("Segoe UI", 9),
                             anchor="w", width=240)
    phase = 0.0
    def animate() -> None:
        nonlocal phase
        phase += 0.12
        offset = int(4 + 4 * (0.5 + 0.5 * math.sin(phase)))
        canvas.coords(circle, 28 - offset, 38 - offset, 78 + offset, 88 + offset)
        root.after(40, animate)
    def check_queue() -> None:
        try:
            while True:
                state, text = _state_queue.get_nowait()
                canvas.itemconfig(circle, fill=COLORS.get(state, COLORS["idle"]))
                canvas.itemconfig(label, text=LABELS.get(state, "Leo"))
                canvas.itemconfig(sub, text=text[:55] + ("..." if len(text) > 55 else ""))
        except queue.Empty:
            pass
        root.after(100, check_queue)
    animate()
    check_queue()
    root.mainloop()


def start_ui() -> None:
    """Launch the compatibility popup in a daemon thread."""
    threading.Thread(target=_run_floating_ui, daemon=True).start()


if __name__ == "__main__":
    run_desktop_app()
