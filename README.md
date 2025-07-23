# Minerva Seat Finder

## Overview

A tiny Python script that logs into Minerva site, fetches seat/waitlist info for a course, and sends a Discord notification when seats (or the waitlist) are available. It’s designed to run locally or on GitHub Actions every 60 minutes.

## Prerequisites

- Python 3.10+
- pip
- A Discord webhook URL
- Your Minerva Student ID and PIN

## Environment Variables

Set these locally (e.g., in a `.env` file):

- student_id -> your McGill Student ID
- password -> your PIN/password
- discord_webhook_url -> Discord channel webhook

## Local Setup & Run

1. Install deps:
   pip install -r requirements.txt

2. Run:
   python main.py COMP 307

   (Replace COMP and 307 with your subject & course.)

3. Output prints seat/waitlist stats. If seats/waitlist are available, it posts to Discord.

## Usage (CLI)

python main.py <SUBJECT> <COURSE>

Examples:
python main.py COMP 307
python main.py MATH 140

## GitHub Actions Automation

- Workflow file: `.github/workflows/comp_307.yml`
- Runs every 60 minutes via cron and can be triggered manually using `workflow_dispatch`.
- Requires:
  - Repo secret `DISCORD_WEBHOOK_URL`
  - Repo (or environment) secrets `STUDENT_ID`, `PASSWORD`
  - `permissions: contents: write` to commit state file

## Discord Notifications

A simple `discord_notify()` sends an embed with:

- Title (e.g., “Seats available for COMP 307!”)
- Description: seat and waitlist numbers.

If you need formatting (bold, code blocks), adjust the payload.

## Extending

- Monitor multiple courses: loop through a list and aggregate messages.
- Store status in Redis/S3 to avoid spamming in case seats are found.

## License / Credits

Use at your own risk. This is an unofficial scraper for personal use. Respect McGill policies.
