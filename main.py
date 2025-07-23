import os
import re
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
    webhook = env_required("DISCORD_WEBHOOK_URL")
    payload = {"embeds": [{"title": title, "description": text}]}
    r = requests.post(webhook, json=payload, timeout=10)
    r.raise_for_status()

def parse_course_list(env_value: str):
    """Parse 'COMP:307,MATH:140' → [('COMP','307'), ('MATH','140')]"""
    pairs = []
    for chunk in env_value.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        if ":" not in chunk:
            raise ValueError(f"Bad course spec '{chunk}', expected SUBJECT:NUMBER")
        subj, num = chunk.split(":", 1)
        pairs.append((subj.strip(), num.strip()))
    return pairs

# ---------- network ----------

def login(session: requests.Session, sid: str, pin: str):
    session.get(LOGIN_FORM_URL, timeout=15)
    payload = {"sid": sid, "PIN": pin}
    r = session.post(LOGIN_URL, data=payload, timeout=15)
    r.raise_for_status()
    if 'twbkwbis.P_GenMenu?name=bmenu.P_MainMnu' not in r.text:
        raise RuntimeError("Login failed.")

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
        ("SUB_BTN", "View Sections"),
    ]
    r = session.get(SECTIONS_URL, params=params, timeout=20)
    r.raise_for_status()
    return r.text

def parse_waitlist(html: str, course: str, subject: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    # strict match of the course number in a cell
    cell = soup.find(string=re.compile(rf"^\s*{re.escape(str(course))}\s*$"))
    if not cell:
        raise RuntimeError(f"Couldn't find course {course} in page.")

    row = cell.find_parent("tr")
    tds = row.find_all("td")
    cols = tds[10:16]
    values = [td.get_text(strip=True) for td in cols]

    data = dict(zip(DATA_MAP, values))
    data["Subject"] = subject
    data["Course"] = course
    return data

# ---------- main ----------

def run_for_course(session, subject, course):
    html = get_course_sections(session, subject, course)
    data = parse_waitlist(html, course, subject)

    lines = [f"{subject} {course}"]
    lines += [f"{k}" for k in DATA_MAP]
    # But ensure order matches DATA_MAP:
    text = "\n".join([f"{subject} {course}"] +
                     [f"{k}: {data[k]}" for k in DATA_MAP])

    print(text)

    if data["Seats Available"] != "0":
        discord_notify(f"Seats available for {subject} {course}!", text)
    elif data["Waitlist Remaining"] != "0":
        discord_notify(f"Waitlist available for {subject} {course}!", text)

def main():
    load_dotenv(override=False)

    sid = env_required("STUDENT_ID")
    pin = env_required("PASSWORD")
    raw_courses = env_required("COURSES")
    course_list = parse_course_list(raw_courses)

    with requests.Session() as sess:
        sess.headers.update({"User-Agent": "Mozilla/5.0"})
        login(sess, sid, pin)

        for subj, num in course_list:
            try:
                run_for_course(sess, subj, num)
            except Exception as ex:
                print(f"[{subj} {num}] error: {ex}")

if __name__ == "__main__":
    main()
