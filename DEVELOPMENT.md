# Development Log

A record of significant features, technical challenges, debugging,
and design decisions made during development. 

<br/>

## August 2026 — Day-Specific Course Schedules

### Problem
Some courses meet at different times depending on the day of the week.

### Example

```text
MW 11:15 AM - 12:00 PM
TH 9:35 AM - 10:50 AM
```

### Result
Added schedule parsing that:
1. Determines the weekday of the assignment deadline.
2. Finds the matching day in the course schedule.
3. Extracts the appropriate class start time.
4. Uses that time when creating the Google Calendar event.
<br/><br/>
## August 2026 — Time Parsing and Debugging

### Problem
Course schedules can represent times in slightly different formats,
such as:

    11 AM
    11:15 AM
    9:35 - 10:50 AM

These formats cannot all be parsed using the same `datetime` format.

### Implementation
Added logic to:

- Extract the start of a class's time range.
- Detect whether the time contains minutes.
- Handle AM/PM information.
- Convert the resulting string into a Python `datetime`.

During development, GitHub Actions logs were used to inspect the actual
values being returned by the program and diagnose parsing errors.

### Result 
The synchronization can correctly interpret the time formats used in the
course schedule.
<br/><br/>
## August 2026 — Day-Specific Course Schedules

### Problem
Some courses meet at different times depending on the day of the week.

For example:

    MW 11:15 AM - 12:00 PM
    TH 9:35 AM - 10:50 AM

Using one fixed time for each course would therefore create incorrect
calendar events.

### Implementation
Added schedule parsing that:

1. Determines the weekday of the assignment deadline.
2. Converts the weekday into the corresponding schedule code.
3. Parses the course's schedule entries.
4. Finds the entry matching that weekday.
5. Extracts the appropriate class start time.
6. Uses that time when creating the Google Calendar event.

### Result
An assignment due on Thursday can be scheduled using the Thursday class
time rather than the Monday/Wednesday class time.
<br/><br/>
## June 2026 — Secure Credential Management

### Problem
The program requires sensitive credentials including the Notion API token
and Google OAuth credentials. These should not be committed to a public
GitHub repository.

### Implementation
- Added sensitive files such as `.env`, `token.json`, and
  `credentials.json` to `.gitignore`.
- Stored credentials in GitHub Actions Secrets.
- Reconstructed the required credential files during workflow execution.
- Used environment variables for configuration such as database IDs and
  calendar IDs.

### Result
The repository can remain public without exposing API tokens or OAuth
credentials.
<br/><br/>
## June 2026 — GitHub Actions Deployment

### Problem
The synchronization worked locally, but required manually running
`sync.py`.

The goal was to make the system operate automatically without relying on
my personal computer being turned on.

### Implementation
- Added a GitHub Actions workflow.
- Configured GitHub Actions to install Python and project dependencies.
- Added the required environment variables and credentials as GitHub
  repository secrets.
- Configured the workflow to execute `sync.py`.
- Added a scheduled cron trigger for automatic execution.
- Retained a manual `workflow_dispatch` trigger for testing.

### Result
The synchronization can run in the cloud without requiring the local
computer to be running.
<br/><br/>
## June 2026 — Assignment Completion Synchronization

### Problem
The initial system could create calendar events, but marking an assignment
as `Done` in Notion did not remove its corresponding calendar event.

### Implementation
Added logic to check the assignment's Notion status.

If the status is `Done`:

1. Check whether a Google Event ID exists.
2. Delete the corresponding Google Calendar event.
3. Clear the Google Event ID from the Notion assignment.

### Result
Completing an assignment in Notion now automatically removes its
corresponding calendar event during the next synchronization.
<br/><br/>
## June 2026 — Duplicate Prevention

### Problem
GitHub Actions would eventually run the synchronization repeatedly.
Without additional logic, every run would create another Google Calendar
event for every assignment.

### Implementation
Before creating an event, the program checks whether the assignment already
contains a Google Event ID.

If one exists, the assignment is skipped.

### Result
Running the synchronization multiple times no longer creates duplicate
calendar events.
