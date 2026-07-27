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
COURSES_DB = os.getenv("COURSES_DATABASE_ID")


# --------------------
# Helper functions
# --------------------

def get_title(prop):
    if not prop["title"]:
        return ""
    return prop["title"][0]["plain_text"]


def get_text(prop):
    if not prop or "rich_text" not in prop:
        return ""

    if not prop["rich_text"]:
        return ""

    return prop["rich_text"][0]["plain_text"]


def get_date(prop):
    return prop["date"]["start"]


def get_relation(prop):
    if not prop["relation"]:
        return None

    return prop["relation"][0]["id"]


# --------------------
# Get course info
# --------------------

def get_course(course_id):

    page = notion.pages.retrieve(course_id)

    props = page["properties"]

    name = get_title(props["Name"])

    time = get_text(props["Time"])

    return name, time


# --------------------
# Google Calendar functions
# --------------------

def create_event(title, date, start_time):

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

    created = calendar.events().insert(
        calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
        body=event
    ).execute()

    return created["id"]


def delete_event(event_id):

    try:
        calendar.events().delete(
            calendarId=os.getenv("GOOGLE_CALENDAR_ID"),
            eventId=event_id
        ).execute()

        return True

    except Exception as e:
        print("Delete failed:", e)
        return False


# --------------------
# Main sync
# --------------------

results = notion.databases.retrieve(
    database_id=DEADLINES_DB
)

data_source = results["data_sources"][0]["id"]

assignments = notion.data_sources.query(
    data_source_id=data_source
)


for assignment in assignments["results"]:

    props = assignment["properties"]

    status = props["Status"]["status"]["name"]

    name = get_title(props["Name"])

    google_event_id = get_text(props["Google Event ID"])


    # --------------------
    # Delete completed tasks
    # --------------------

    if status == "Done":

        if google_event_id:

            deleted = delete_event(google_event_id)

            if deleted:
                print("Deleted:", name)

                notion.pages.update(
                    page_id=assignment["id"],
                    properties={
                        "Google Event ID": {
                            "rich_text": []
                        }
                    }
                )

        continue


    # --------------------
    # Create new events
    # --------------------

    deadline = get_date(props["Deadline"])

    course_id = get_relation(props["Course"])

    if not course_id:
        print("No course:", name)
        continue


    course_name, course_time = get_course(course_id)

    title = f"{name} - {course_name}"


    # Prevent duplicates

    if google_event_id:
        print("Already synced:", title)
        continue


    event_id = create_event(
        title,
        deadline,
        course_time
    )


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
