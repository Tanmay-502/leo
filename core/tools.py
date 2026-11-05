"""Validated tools exposed to Leo's language model."""

from __future__ import annotations

import base64
import re
import subprocess
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from urllib.parse import quote

import requests
try:
    from langchain_core.tools import tool
except ImportError:
    class _LocalTool:
        def __init__(self, func):
            self.func, self.name, self.description = func, func.__name__, func.__doc__ or ""
        def __call__(self, *args, **kwargs):
            return self.func(*args, **kwargs)
        def invoke(self, args):
            return self.func(**args)

    def tool(func):
        return _LocalTool(func)
try:
    import feedparser
except ImportError:
    feedparser = None
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None
try:
    from googleapiclient.discovery import build
except ImportError:
    build = None

from core.google_auth import get_google_credentials
from core.memory import clear_conversation, delete_fact, get_all_facts, save_fact

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
APP_MAP = {
    "chrome": ["chrome"],
    "notepad": ["notepad"],
    "calculator": ["calc"],
    "vs code": ["code"],
    "vscode": ["code"],
    "explorer": ["explorer"],
    "file explorer": ["explorer"],
}


@tool
def check_calendar(time_range: str = "today") -> str:
    """Check calendar for today, tomorrow, or this week."""
    try:
        if build is None:
            return "Google integration dependencies are not installed."
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)
        now = datetime.now(timezone.utc)
        lowered = time_range.lower()
        if "tomorrow" in lowered:
            start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif "week" in lowered:
            start = now
        else:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=7 if "week" in lowered else 1)
        result = service.events().list(
            calendarId="primary", timeMin=start.isoformat(), timeMax=end.isoformat(),
            singleEvents=True, orderBy="startTime",
        ).execute()
        events = result.get("items", [])
        if not events:
            return f"No meetings scheduled for {time_range}."
        summaries = []
        for event in events[:5]:
            when = event.get("start", {}).get("dateTime", event.get("start", {}).get("date", "unknown"))
            summaries.append(f"{event.get('summary', 'Untitled')} at {when}")
        return f"{len(events)} meeting(s) {time_range}: " + " | ".join(summaries)
    except Exception:
        return "I couldn't access your calendar. Check Google credentials and permissions."


@tool
def schedule_meeting(title: str, start_time: str, attendees: str = "", duration_minutes: int = 60) -> str:
    """Schedule a calendar event after the user confirms its details."""
    if not title.strip() or duration_minutes < 1 or duration_minutes > 1440:
        return "Please provide a title and a duration between 1 and 1440 minutes."
    try:
        start = datetime.fromisoformat(start_time)
    except ValueError:
        return "Use an ISO date/time such as 2026-11-05T14:00:00+05:30."
    emails = [item.strip() for item in attendees.split(",") if item.strip()]
    if any(not EMAIL_RE.fullmatch(email) for email in emails):
        return "One or more attendee email addresses are invalid."
    try:
        if build is None:
            return "Google integration dependencies are not installed."
        service = build("calendar", "v3", credentials=get_google_credentials())
        end = start + timedelta(minutes=duration_minutes)
        body = {
            "summary": title.strip(),
            "start": {"dateTime": start.isoformat()},
            "end": {"dateTime": end.isoformat()},
        }
        if emails:
            body["attendees"] = [{"email": email} for email in emails]
        created = service.events().insert(calendarId="primary", body=body).execute()
        return f"'{title.strip()}' scheduled successfully. Link: {created.get('htmlLink', 'available in Calendar')}."
    except Exception:
        return "I couldn't schedule that meeting. Check Google credentials and permissions."


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email only after the user confirms recipient, subject, and body."""
    recipients = [item.strip() for item in to.split(",") if item.strip()]
    if not recipients or any(not EMAIL_RE.fullmatch(email) for email in recipients):
        return "Please provide valid recipient email addresses."
    if not subject.strip() or not body.strip():
        return "Email subject and body cannot be empty."
    try:
        message = MIMEText(body)
        message["to"] = ", ".join(recipients)
        message["subject"] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        if build is None:
            return "Google integration dependencies are not installed."
        build("gmail", "v1", credentials=get_google_credentials()).users().messages().send(
            userId="me", body={"raw": raw}
        ).execute()
        return f"Email sent to {', '.join(recipients)} — '{subject}'."
    except Exception:
        return "I couldn't send the email. Check Google credentials and permissions."


@tool
def fetch_unread_emails() -> str:
    """Fetch a short summary of unread inbox emails."""
    try:
        if build is None:
            return "Google integration dependencies are not installed."
        service = build("gmail", "v1", credentials=get_google_credentials())
        result = service.users().messages().list(
            userId="me", labelIds=["UNREAD", "INBOX"], maxResults=5
        ).execute()
        messages = result.get("messages", [])
        if not messages:
            return "No unread emails."
        summaries = []
        for message in messages:
            data = service.users().messages().get(
                userId="me", id=message["id"], format="metadata",
                metadataHeaders=["Subject", "From"],
            ).execute()
            headers = {h["name"]: h["value"] for h in data.get("payload", {}).get("headers", [])}
            summaries.append(f"'{headers.get('Subject', 'No subject')}' from {headers.get('From', 'Unknown sender')}")
        return f"{len(messages)} unread email(s): " + " | ".join(summaries)
    except Exception:
        return "I couldn't access unread email. Check Google credentials and permissions."


@tool
def daily_summary() -> str:
    """Summarize today's calendar and unread mail."""
    return f"Today: {check_calendar.invoke({'time_range': 'today'})} Also, {fetch_unread_emails.invoke({})}"


@tool
def remember_fact(fact: str) -> str:
    """Remember an explicit user preference or fact."""
    if not fact.strip():
        return "Tell me the fact you want me to remember."
    save_fact(fact)
    return f"Got it, I'll remember: {fact.strip()}"


@tool
def list_memories() -> str:
    """List facts explicitly saved about the user."""
    facts = get_all_facts()
    return "I don't have any saved facts." if not facts else "I remember: " + "; ".join(facts)


@tool
def forget_memory(query: str) -> str:
    """Delete saved facts matching a phrase."""
    deleted = delete_fact(query)
    return f"Forgot {deleted} saved fact(s)." if deleted else "I couldn't find a saved fact matching that."


@tool
def clear_conversation_history() -> str:
    """Delete short-term conversation history without deleting saved facts."""
    clear_conversation()
    return "Conversation history cleared. Saved facts were kept."


@tool
def get_weather(city: str) -> str:
    """Get current temperature, conditions, and wind for a city."""
    if not city.strip():
        return "Please provide a city."
    try:
        geo = requests.get(
            f"https://geocoding-api.open-meteo.com/v1/search?name={quote(city)}&count=1",
            timeout=5,
        )
        geo.raise_for_status()
        results = geo.json().get("results", [])
        if not results:
            return f"Couldn't find location '{city}'."
        loc = results[0]
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={"latitude": loc["latitude"], "longitude": loc["longitude"], "current_weather": "true"},
            timeout=5,
        )
        response.raise_for_status()
        current = response.json().get("current_weather")
        if not current:
            return "Weather data is unavailable right now."
        return f"{loc.get('name', city)}: {current['temperature']}°C, wind {current['windspeed']} km/h."
    except (requests.RequestException, ValueError, KeyError):
        return "I couldn't fetch weather right now."


@tool
def web_search(query: str) -> str:
    """Search the web and return concise linked results."""
    if not query.strip():
        return "Please provide a search query."
    try:
        if DDGS is None:
            return "Search dependencies are not installed."
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        return " | ".join(
            f"{item.get('title', 'Result')}: {item.get('body', '')[:160]} ({item.get('href', '')})"
            for item in results
        )
    except Exception:
        return "Search is unavailable right now."


@tool
def get_news(topic: str = "general") -> str:
    """Get current headlines, optionally filtered by topic."""
    try:
        if feedparser is None:
            return "News dependencies are not installed."
        feed = feedparser.parse("https://feeds.bbci.co.uk/news/rss.xml")
        entries = feed.entries
        if topic and topic.lower() != "general":
            entries = [entry for entry in entries if topic.lower() in entry.get("title", "").lower() or topic.lower() in entry.get("summary", "").lower()]
        if not entries:
            return "No matching news is available."
        return " | ".join(f"{entry.title} ({entry.get('link', '')})" for entry in entries[:5])
    except Exception:
        return "News is unavailable right now."


@tool
def open_app(app_name: str) -> str:
    """Open one of Leo's registered desktop applications safely."""
    command = APP_MAP.get(app_name.lower().strip())
    if not command:
        return f"I don't know how to open '{app_name}' yet."
    try:
        subprocess.Popen(command, shell=False)
        return f"Opening {app_name}."
    except (OSError, ValueError):
        return f"I couldn't find or open {app_name}."


ALL_TOOLS = [
    check_calendar, schedule_meeting, send_email, fetch_unread_emails, daily_summary,
    get_weather, web_search, get_news, open_app, remember_fact, list_memories,
    forget_memory, clear_conversation_history,
]
