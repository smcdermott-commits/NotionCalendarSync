from notion_client import Client
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

load_dotenv()

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

def get_title(prop):
    if not prop["title"]:
        return ""
    return prop["title"][0]["plain_text"]


def get_text(prop):
    if not prop or "rich_text" not in prop:            # Check if property exists and contains anything
        return ""

    if not prop["rich_text"]:                          # Check if property has rich text field
        return ""

    return prop["rich_text"][0]["plain_text"]          # Returns first plain text item in property


def get_date(prop):
    return prop["date"]["start"]


def get_relation(prop):
    if not prop["relation"]:
        return None

    return prop["relation"][0]["id"]


# --------------------
# Get course info
# --------------------

def get_course(course_id):                            # Retrieves course info from related page

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


def parse_days(days):                                   # Converts block of days into list of day codes course takes place on (Ex. MWF = [M, W, F])
    result = []
    i = 0

    while i < len(days):                                # TH and SU are special cases for parsing day of week of course, otherwise day codes correlate
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


def get_start_time(schedule, date):        # Some classes meet at different times on different days of the week, so function compares due date with listed day to see which line applies

    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")       # Converts due date listed in assignment tracker to string day of the week (ex. 2026-08-11 returns as Tuesday)
    code = DAY_CODES[weekday]

    for line in schedule.splitlines():                                 # Splits multi-line entries in schedule into separate strings, one for each line

        line = line.strip()                                            # Removes unecessary spaces

        if not line:                                                   # Skips empty lines
            continue

        parts = line.split(" ", 1)                                     # Only splits line into multiple strings at first space (Ex. "MW 11 - 11:50 AM" turns into ["MW", "11 - 11:50 AM"])

        if len(parts) != 2:                                            # Checks that line is split into only 2 strings; if it's wrong, program skips entire line to prevent it from breaking
            continue

        days = parts[0]                                                # Assigns first part of line as days and second part as times
        times = parts[1]

        if code in parse_days(days):                                   # Runs function parse_days to return list of days class meets listed in current line; if week day of assignmnet due date is 
            return times.split("-")[0].strip()                         # listed in this line, take the times and split into start and end time (Ex. "11:15 AM - 12:00 PM" --> ["11:15 AM "," 12:00 PM"]),
                                                                       # then only takes 1st item (start time)

    return None
    
def create_event(title, date, schedule):

    start_time = get_start_time(schedule, date)

    if start_time is None:
        raise Exception(
            f"No meeting time found for {title} on {date}"
        )
        
    weekday = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
    code = DAY_CODES[weekday]

    period = None                                                # New variable for AM/PM

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

                                                                    # Look for AM/PM anywhere in line for cases like "8:10 - 9:25 AM" where both times are AM/PM
            if "AM" in times.upper():
                period = "AM"
            elif "PM" in times.upper():
                period = "PM"

            break

    if period is None:
        raise Exception(
            f"Could not determine AM/PM for {title} on {date}"
        )

                                                                    # Add AM/PM if the start time doesn't already have it
    if "AM" not in start_time.upper() and "PM" not in start_time.upper():
        start_time = f"{start_time} {period}"

    
                                                                # Figure out if format is "11 AM" or "11:15 AM"; converts to HH:MM if no minutes are listed (at top of hour)
    if ":" in start_time:
        fmt = "%Y-%m-%d %I:%M %p"
    else:
        fmt = "%Y-%m-%d %I %p"

    dt = datetime.strptime(
        f"{date} {start_time}",
        fmt
    )

    end = dt + timedelta(minutes=1)                    # End time is 1 minute after start

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


for assignment in assignments["results"]:                    # Lists properties for each assignment in database

    props = assignment["properties"]

    status = props["Status"]["status"]["name"]

    name = get_title(props["Name"])

    google_event_id = get_text(props["Google Event ID"])


    # --------------------
    # Delete completed tasks
    # --------------------

    if status == "Done":                                    # If property "Status" is set to "Done", deletes google calendar event

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

    title = f"{name} - {course_name}"                    # Combines assignment name and course name to make title listed on google calendar event (Ex. Problem Set 3 - Physics)


    # Prevent duplicates

    if google_event_id:                                # If there is already a google event id in that property, program recognizes that the event has already been created and verifies that info is up to date
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
