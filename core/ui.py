# core/ui.py
# A small floating popup window that shows Leo's current state — listening,
# thinking, or speaking — similar to Siri's activation indicator.
# Runs in its own thread so it doesn't block voice/LLM processing.

import tkinter as tk
import threading
import queue
import math

_state_queue = queue.Queue()

COLORS = {
    "listening": "#3B82F6",
    "thinking": "#F59E0B",
    "speaking": "#10B981",
    "idle": "#4B5563",
}

LABELS = {
    "listening": "Listening",
    "thinking": "Thinking",
    "speaking": "Speaking",
    "idle": "Leo",
}

BG = "#0F0F14"
CARD_BG = "#1A1A22"
TEXT_MAIN = "#F5F5F7"
TEXT_SUB = "#9CA3AF"


def set_state(state: str, text: str = ""):
    """Called from voice_loop.py to update what the popup shows."""
    _state_queue.put((state, text))


def _run_ui():
    root = tk.Tk()
    root.title("Leo")
    W, H = 360, 130

    screen_w = root.winfo_screenwidth()
    x = (screen_w - W) // 2
    root.geometry(f"{W}x{H}+{x}+30")
    root.attributes("-topmost", True)
    root.overrideredirect(True)
    root.configure(bg=BG)

    canvas = tk.Canvas(root, width=W, height=H, bg=BG, highlightthickness=0)
    canvas.pack()

    def rounded_rect(x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
            x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1
        ]
        return canvas.create_polygon(points, smooth=True, **kwargs)

    rounded_rect(6, 6, W-6, H-6, 22, fill=CARD_BG, outline="")

    circle = canvas.create_oval(28, 38, 78, 88, fill=COLORS["idle"], outline="")
    label = canvas.create_text(100, 50, text=LABELS["idle"], fill=TEXT_MAIN,
                                font=("Segoe UI", 15, "bold"), anchor="w")
    sub_label = canvas.create_text(100, 76, text="", fill=TEXT_SUB,
                                    font=("Segoe UI", 9), anchor="w", width=240)

    pulse = {"phase": 0.0}

    def animate():
        pulse["phase"] += 0.12
        offset = int(4 + 4 * (0.5 + 0.5 * math.sin(pulse["phase"])))
        canvas.coords(circle, 28 - offset, 38 - offset, 78 + offset, 88 + offset)
        root.after(40, animate)

    def check_queue():
        try:
            while True:
                state, text = _state_queue.get_nowait()
                canvas.itemconfig(circle, fill=COLORS.get(state, COLORS["idle"]))
                canvas.itemconfig(label, text=LABELS.get(state, "Leo"))
                display_text = text[:55] + "..." if len(text) > 55 else text
                canvas.itemconfig(sub_label, text=display_text)
        except queue.Empty:
            pass
        root.after(100, check_queue)

    animate()
    check_queue()
    root.mainloop()


def start_ui():
    """Launches the popup UI in a background thread. Call once at startup."""
    ui_thread = threading.Thread(target=_run_ui, daemon=True)
    ui_thread.start()