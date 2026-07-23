# core/tools.py
# This file holds every "ability" Leo has — each function here is a TOOL
# that the LLM (the brain) can decide to call on its own based on what the user says.
# Right now these are STUBS (fake responses) so we can test the routing logic
# before wiring up real Google APIs. Only this file will change later — agent.py won't.

from langchain_core.tools import tool  
# @tool decorator turns a normal python function into something the LLM can "see" and call

@tool
def check_calendar(time_range: str = "today"):
    """Check the user's calendar for a given time range (e.g. 'today', 'tomorrow', 'this week')."""
    # The docstring above is IMPORTANT — the LLM reads it to decide WHEN to use this tool.
    # STUB response for now:
    return f"[STUB] You have 2 meetings {time_range}: 'Bitsquad Standup' at 10 AM and 'Project Sync' at 3 PM."

@tool
def schedule_meeting(title: str, start_time: str, attendees: str = ""):
    """Schedule a new meeting with a title, start time, and optional attendees."""
    return f"[STUB] Meeting '{title}' scheduled at {start_time} with attendees: {attendees or 'none'}."

@tool
def send_email(to: str, subject: str, body: str):
    """Send an email to a recipient with a subject and body."""
    return f"[STUB] Email sent to {to} — Subject: '{subject}'."

@tool
def fetch_unread_emails():
    """Fetch and summarize the user's unread emails."""
    return "[STUB] You have 3 unread emails: 1 from Bitsquad HR (policy update), 2 newsletters."

@tool
def daily_summary():
    """Give a summary of the user's day — calendar + emails combined."""
    # This tool shows the LLM can also call functions that look "combined" —
    # later we can make this ACTUALLY call check_calendar + fetch_unread_emails internally.
    return "[STUB] Today: 2 meetings, 3 unread emails, no urgent deadlines."

# We bundle all tools into one list so agent.py can import just this ONE variable
# instead of importing every function separately. Cleaner and easier to extend.
ALL_TOOLS = [check_calendar, schedule_meeting, send_email, fetch_unread_emails, daily_summary]