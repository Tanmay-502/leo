# core/tools.py
# Leo's tool functions. Docstrings are kept SHORT on purpose — every tool's
# description gets sent to the LLM on EVERY message (since they're all bound
# together), so shorter docstrings = fewer tokens per call = less chance of
# hitting the free tier's per-minute token limit.

from langchain_core.tools import tool

@tool
def check_calendar(time_range: str = "today"):
    """Check calendar for a time range like 'today' or 'tomorrow'."""
    return f"[STUB] 2 meetings {time_range}: Standup 10AM, Project Sync 3PM."

@tool
def schedule_meeting(title: str, start_time: str, attendees: str = ""):
    """Schedule a meeting with title, start time, and attendees."""
    return f"[STUB] '{title}' scheduled at {start_time} with {attendees or 'none'}."

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

ALL_TOOLS = [check_calendar, schedule_meeting, send_email, fetch_unread_emails, daily_summary]