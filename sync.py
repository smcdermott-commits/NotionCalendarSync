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
DAY_CODES = {
    "Monday": "M",
    "Tuesday": "T",
    "Wednesday": "W",
    "Thursday": "TH",
    "Friday": "F",
    "Saturday": "S",
    "Sunday": "SU"
}


def parse_days(days):
    result = []
    i = 0

    while i < len(days):
        if days.startswith("TH", i):
            result.append("TH")
            i += 2
        elif days.startswith("SU", i):
            result.append("SU")
            i += 2
        else:
            result.append(days[i])
            i += 1

    return result


def get_start_time(schedule, date):

    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    code = DAY_CODES[weekday]

    for line in schedule.splitlines():

        line = line.strip()

        if not line:
            continue

        parts = line.split(" ", 1)

        if len(parts) != 2:
            continue

        days = parts[0]
        times = parts[1]

        if code in parse_days(days):
            return times.split("-")[0].strip()

    return None
    
def create_event(title, date, schedule):

    start_time = get_start_time(schedule, date)

    if start_time is None:
        raise Exception(
            f"No meeting time found for {title} on {date}"
        )

    # Supports both "11 AM" and "11:15 AM"
    if ":" in start_time:
        fmt = "%Y-%m-%d %I:%M %p"
    else:
        fmt = "%Y-%m-%d %I %p"

    dt = datetime.strptime(
        f"{date} {start_time}",
        fmt
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
