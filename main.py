import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

TERM = "202601"
DATA_MAP = ["Seats", "Seats Taken", "Seats Available",
            "Waitlist Capacity", "Waitlist Total", "Waitlist Remaining"]

LOGIN_FORM_URL = "https://horizon.mcgill.ca/pban1/twbkwbis.P_WWWLogin"
LOGIN_URL = "https://horizon.mcgill.ca/pban1/twbkwbis.P_ValLogin"
SECTIONS_URL = "https://horizon.mcgill.ca/pban1/bwskfcls.P_GetCrse"

# ---------- helpers ----------

def env_required(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing required env var {name}")
    return val

def discord_notify(title: str, text: str):
    webhook = env_required("discord_webhook_url")
    payload = {"embeds": [{"title": title, "description": text}]}
    r = requests.post(webhook, json=payload, timeout=10)
    r.raise_for_status()

# ---------- core logic ----------

def login(session: requests.Session, sid: str, pin: str) -> None:
    r = session.get(LOGIN_FORM_URL, timeout=15)
    r.raise_for_status()

    resp = session.post(LOGIN_URL, params={"sid": sid, "PIN": pin}, timeout=15)
    resp.raise_for_status()
    ok = '<meta http-equiv="refresh" content="0;url=/pban1/twbkwbis.P_GenMenu?name=bmenu.P_MainMnu">' in resp.text
    if not ok:
        raise RuntimeError("Login failed (did not find refresh meta tag).")

def get_course_sections(session: requests.Session, subject: str, course: str) -> str:
    params = [
        ("term_in", TERM),
        ("sel_subj", "dummy"),
        ("sel_subj", subject),
        ("SEL_CRSE", course),
        ("SEL_TITLE", ""),
        ("BEGIN_HH", "0"), ("BEGIN_MI", "0"), ("BEGIN_AP", "a"),
        ("SEL_DAY", "dummy"), ("SEL_PTRM", "dummy"),
        ("END_HH", "0"), ("END_MI", "0"), ("END_AP", "a"),
        ("SEL_CAMP", "dummy"), ("SEL_SCHD", "dummy"),
        ("SEL_SESS", "dummy"),
        ("SEL_INSTR", "dummy"), ("SEL_INSTR", "%"),
        ("SEL_ATTR", "dummy"), ("SEL_ATTR", "%"),
        ("SEL_LEVL", "dummy"), ("SEL_LEVL", "%"),
        ("SEL_INSM", "dummy"),
        ("sel_dunt_code", ""), ("sel_dunt_unit", ""),
        ("call_value_in", ""), ("rsts", "dummy"),
        ("crn", "dummy"), ("path", "1"),
        ("SUB_BTN", "View Sections")
    ]
     
    resp = session.get(SECTIONS_URL, params=params, timeout=20)
    resp.raise_for_status()
    return resp.text

def parse_waitlist(html: str, course: str, subject: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    
    cell = soup.find(string=course)
    if not cell:
        raise RuntimeError(f"Couldn't find course {course} in page.")
    row = cell.find_parent("tr")

    cols = row.find_all("td")[10:16]
    values = [c.get_text(strip=True) for c in cols]
    data = dict(zip(DATA_MAP, values))
    data["Subject"] = subject
    data["Course"] = course
    return data

def run(subject: str, course: str):
    sid = env_required("student_id")
    pin = env_required("password")

    with requests.Session() as s:
        login(s, sid, pin)
        html = get_course_sections(s, subject, course)
        data = parse_waitlist(html, course, subject)

    lines = [f"{subject} {course}"]
    lines += [f"{k}: {v}" for k, v in data.items() if k in DATA_MAP]
    text = "\n".join(lines)

    print(text)

    seats_rem = data["Seats Available"]
    wl_rem = data["Waitlist Remaining"]

    if seats_rem != "0":
        discord_notify(f"Seats available for {subject} {course}!", text)
    elif wl_rem != "0":
        discord_notify(f"Waitlist available for {subject} {course}!", text)

# ---------- CLI ----------

def parse_args(argv):
    p = argparse.ArgumentParser()
    p.add_argument("subject")
    p.add_argument("course")
    return p.parse_args(argv)

if __name__ == "__main__":
    load_dotenv()
    args = parse_args(sys.argv[1:])
    run(args.subject, args.course)