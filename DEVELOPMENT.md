# Development Log

A record of significant features, technical challenges, debugging,
and design decisions made during development. 

<br/>

<details><summary><h2>August 2026 — Explicit Assignment Times</h2></summary>

### Problem
Some assignments are due at a specific time that differs from the normal
class meeting time. Others may be due on a day when the course does not
meet at all.

Using the course schedule in these cases could result in an incorrect
Google Calendar event time.

### Implementation
Updated the deadline handling to account for optional times specified
directly in Notion.

The synchronization now:

1. Checks whether the Notion deadline includes a specific time.
2. Uses the specified start time when one is provided.
3. Uses the specified end time when a time range is provided.
4. Falls back to the course's scheduled class time when no time is
   specified.
5. Defaults to 10:00 AM when no time is specified and the course does not
   meet on that day.
6. Uses the appropriate event duration based on whether an explicit time
   range was provided.

### Result
Assignments with specific times in Notion now take priority over the
course schedule, while assignments without specified times continue to
use the appropriate class meeting time or the 10:00 AM fallback. </details>

<details><summary><h2> August 2026 — Calendar Event Visibility </h2></summary>

### Problem
The synchronization initially created very short Google Calendar events,
making assignments difficult to distinguish visually in the calendar.

### Implementation
Increased the default Google Calendar event duration from 1 minute to
30 minutes.

The event still represents the assignment deadline rather than the actual
class duration, but the longer duration makes assignments easier to see
and identify when viewing the calendar.

### Result
Assignment events are now displayed as 30-minute blocks in Google Calendar,
making deadlines more visually prominent and easier to distinguish from
other calendar events. </details>


<details><summary><h2> August 2026 — Day-Specific Course Schedules </h2></summary>

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
</details>

<details><summary><h2> June 2026 — Secure Credential Management </h2></summary>

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
</details>

<details><summary><h2> June 2026 — GitHub Actions Deployment </h2></summary>

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
</details>

<details><summary><h2> June 2026 — Assignment Completion Synchronization </h2></summary>

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
</details>

<details><summary><h2> June 2026 — Duplicate Prevention</h2></summary>

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
</details>
