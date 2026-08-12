# core/tools.py
# Leo's tool functions. Docstrings are kept SHORT on purpose — every tool's
# description gets sent to the LLM on EVERY message (since they're all bound
# together), so shorter docstrings = fewer tokens per call = less chance of
# hitting the free tier's per-minute token limit.

import os
import requests
from langchain_core.tools import tool
from ddgs import DDGS
import feedparser
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from core.google_auth import get_google_credentials

# PRODUCTIVITY TOOLS (stubs — real Google API comes later)

@tool
def check_calendar(time_range: str = "today"):
    """Check calendar for a time range like 'today' or 'tomorrow'."""
    try:
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)

        # Figure out the date window based on what the user asked for
        now = datetime.utcnow()
        if "tomorrow" in time_range.lower():
            start = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif "week" in time_range.lower():
            start = now
        else:  # default to "today"
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        end = start + timedelta(days=7 if "week" in time_range.lower() else 1)

        events_result = service.events().list(
            calendarId="primary",
            timeMin=start.isoformat() + "Z",
            timeMax=end.isoformat() + "Z",
            singleEvents=True,
            orderBy="startTime",
        ).execute()

        events = events_result.get("items", [])

        if not events:
            return f"No meetings scheduled for {time_range}."

        summary = []
        for event in events[:5]:  # cap at 5 to keep token cost low
            start_time = event["start"].get("dateTime", event["start"].get("date"))
            summary.append(f"{event.get('summary', 'Untitled')} at {start_time}")

        return f"{len(events)} meeting(s) {time_range}: " + " | ".join(summary)

    except Exception as e:
        return f"Couldn't fetch calendar right now ({e})."


@tool
def schedule_meeting(title: str, start_time: str, attendees: str = ""):
    """Schedule a meeting with title, start time, and attendees."""
    try:
        creds = get_google_credentials()
        service = build("calendar", "v3", credentials=creds)

        # NOTE: start_time needs to be in ISO format for this to work reliably.
        # Real production version would parse natural language dates here —
        # for now we expect something like "2026-08-15T15:00:00"
        end_time_dt = datetime.fromisoformat(start_time) + timedelta(hours=1)

        event = {
            "summary": title,
            "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time_dt.isoformat(), "timeZone": "Asia/Kolkata"},
        }

        if attendees:
            event["attendees"] = [{"email": e.strip()} for e in attendees.split(",")]

        created_event = service.events().insert(calendarId="primary", body=event).execute()

        return f"'{title}' scheduled successfully. Link: {created_event.get('htmlLink')}"

    except Exception as e:
        return f"Couldn't schedule the meeting ({e})."

@tool
def send_email(to: str, subject: str, body: str):
    """Send an email with recipient, subject, and body."""
    return f"[STUB] Email sent to {to} — '{subject}'."

@tool
def fetch_unread_emails():
    """Fetch and summarize unread emails."""
    return "[STUB] 3 unread: 1 HR policy update, 2 newsletters."

@tool
def daily_summary():
    """Summarize the day — calendar + emails."""
    return "[STUB] 2 meetings, 3 unread emails, no urgent deadlines."


# INFORMATION TOOLS (real, live data)

@tool
def get_weather(city: str):
    """Get current weather for a city."""
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
        geo_res = requests.get(geo_url, timeout=5).json()

        if not geo_res.get("results"):
            return f"Couldn't find location '{city}'."

        loc = geo_res["results"][0]
        lat, lon = loc["latitude"], loc["longitude"]

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = requests.get(weather_url, timeout=5).json()
        current = weather_res["current_weather"]

        return f"{city}: {current['temperature']}°C, wind {current['windspeed']} km/h."
    except Exception as e:
        return f"Couldn't fetch weather right now ({e})."


@tool
def web_search(query: str):
    """Search the web for info."""
    try:
        results = DDGS().text(query, max_results=3)
        if not results:
            return "No results found."
        summary = " | ".join(r["body"][:100] for r in results)
        return summary
    except Exception as e:
        return f"Search failed right now ({e})."


@tool
def get_news(topic: str = "general"):
    """Get top news headlines."""
    try:
        feed_url = "http://feeds.bbci.co.uk/news/rss.xml"
        feed = feedparser.parse(feed_url)
        headlines = [entry.title for entry in feed.entries[:5]]
        return " | ".join(headlines)
    except Exception as e:
        return f"Couldn't fetch news right now ({e})."


# SYSTEM TOOLS (local machine control)

APP_MAP = {
    "chrome": "chrome",
    "notepad": "notepad",
    "calculator": "calc",
    "vs code": "code",
    "vscode": "code",
    "explorer": "explorer",
    "file explorer": "explorer",
}

@tool
def open_app(app_name: str):
    """Open a desktop app by name."""
    key = app_name.lower().strip()
    command = APP_MAP.get(key)

    if not command:
        return f"I don't know how to open '{app_name}' yet."

    try:
        os.system(f"start {command}")
        return f"Opening {app_name}."
    except Exception as e:
        return f"Couldn't open {app_name} ({e})."


# BUNDLE — everything Leo can do
ALL_TOOLS = [
    check_calendar, schedule_meeting, send_email, fetch_unread_emails, daily_summary,
    get_weather, web_search, get_news, open_app,
]