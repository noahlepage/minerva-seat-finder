# Minerva Seat Finder

## Overview

A tiny Python script that logs into Minerva site, fetches seat/waitlist info for a course, and sends a Discord notification when seats (or the waitlist) are available. It’s designed to run locally or on GitHub Actions every 60 minutes.

## Prerequisites

- Python 3.10+
- pip
- A Discord webhook URL
- Your Minerva Student ID and PIN

## Environment Variables

Set these locally (e.g., in a `.env` file) and your Github repo:

- STUDENT_ID -> your McGill Student ID
- PASSWORD -> your Minerva PIN
- DISCORD_WEBHOOK_URL -> Discord channel webhook
- COURSES -> Comma-separated list of courses you wish to fetch (ex. COMP:202,MATH:140)

## Local Setup & Run

1. Install deps:
   pip install -r requirements.txt

2. Run:
   python main.py

3. Output prints seat/waitlist stats. If seats/waitlist are available, it posts to Discord.

## GitHub Actions Automation

- Workflow file: `.github/workflows/find-seats.yml`
- Runs every 60 minutes via cron and can be triggered manually using `workflow_dispatch`.
- Requires:
  - Repo secrets `DISCORD_WEBHOOK_URL`, `STUDENT_ID`, `PASSWORD`
  - Environment variable `COURSES`

## Discord Notifications

A simple `discord_notify()` sends an embed with:

- Title (e.g., “Seats available for COMP 202!”)
- Description: seat and waitlist numbers.

If you need formatting (bold, code blocks), adjust the payload.

## Extending

- Store status in Redis/S3 to avoid spamming in case seats are found.

## License / Credits

Use at your own risk. This is an unofficial scraper for personal use. Respect McGill policies.
