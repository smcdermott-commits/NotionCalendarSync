from notion_client import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv()

# --------------------
# Setup
# --------------------

notion = Client(auth=os.getenv("NOTION_TOKEN"))

SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = Credentials.from_authorized_user_file(
    "token.json",
    SCOPES
)

calendar = build(
    "calendar",
    "v3",
    credentials=creds
)

DEADLINES_DB = os.getenv("DEADLINES_DATABASE_ID")


# --------------------
# Helper functions
# --------------------

def get_title(prop):
    return prop["title"][0]["plain_text"]


def get_text(prop):
    if not prop or "rich_text" not in prop:
        return ""

    return prop["rich_text"][0]["plain_text"] if prop["rich_text"] else ""


def get_date(prop):
    return prop["date"]["start"]


def get_relation(prop):
    return prop["relation"][0]["id"]


def get_google_event_id(prop):
    if not prop or "rich_text" not in prop:
        return ""

    if prop["rich_text"]:
        return prop["rich_text"][0]["plain_text"]

    return ""


# --------------------
# Get course information
# --------------------

def get_course(course_id):

    page = notion.pages.retrieve(course_id)

    props = page["properties"]

    name = get_title(props["Name"])

    time = get_text(props["Time"])

    return name, time


# --------------------
# Create or update Google event
# --------------------

def sync_event(title, date, start_time, existing_event_id=None):

    # Example:
    # "10:30 AM - 11:45 AM"
    # becomes:
    # "10:30 AM"

    start_time = start_time.split("-")[0].strip()

    dt = datetime.strptime(
        f"{date} {start_time}",
        "%Y-%m-%d %I:%M %p"
    )

    end = dt + timedelta(minutes=1)

    event = {
        "summary": title,
        "start": {
            "dateTime": dt.isoformat(),
            "timeZone": "America/Los_Angeles"
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": "America/Los_Angeles"
        }
    }

    # Update existing event
    if existing_event_id:

        updated = calendar.events().update(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            eventId=existing_event_id,
            body=event
        ).execute()

        return updated["id"]

    # Create new event
    else:

        created = calendar.events().insert(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            body=event
        ).execute()

        return created["id"]


# --------------------
# Main sync
# --------------------

database = notion.databases.retrieve(
    database_id=DEADLINES_DB
)

data_source_id = database["data_sources"][0]["id"]

assignments = notion.data_sources.query(
    data_source_id=data_source_id
)


for assignment in assignments["results"]:

    props = assignment["properties"]

    status = props["Status"]["status"]["name"]

    # Skip completed assignments for now
    if status == "Done":
        continue


    name = get_title(props["Name"])

    deadline = get_date(props["Deadline"])

    course_id = get_relation(props["Course"])

    course_name, course_time = get_course(course_id)

    title = f"{name} - {course_name}"


    existing_event_id = get_google_event_id(
        props["Google Event ID"]
    )


    event_id = sync_event(
        title,
        deadline,
        course_time,
        existing_event_id
    )


    # Save event ID if it was newly created
    if not existing_event_id:

        notion.pages.update(
            page_id=assignment["id"],
            properties={
                "Google Event ID": {
                    "rich_text": [
                        {
                            "text": {
                                "content": event_id
                            }
                        }
                    ]
                }
            }
        )

        print("Created:", title)

    else:
        print("Updated:", title)
