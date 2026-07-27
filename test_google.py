from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os

SCOPES = ["https://www.googleapis.com/auth/calendar"]

creds = None

# Load existing login if it exists
if os.path.exists("token.json"):
    creds = Credentials.from_authorized_user_file(
        "token.json",
        SCOPES
    )

# If no login exists, ask Google
if not creds:
    flow = InstalledAppFlow.from_client_secrets_file(
        "credentials.json",
        SCOPES
    )

    creds = flow.run_local_server(port=0)

    # Save login for future runs
    with open("token.json", "w") as token:
        token.write(creds.to_json())

service = build(
    "calendar",
    "v3",
    credentials=creds
)

print("Google Calendar connected!")
