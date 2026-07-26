"""
Demo Data Seeder for SchoolHub
==============================

Fills a school account with realistic demo data for client demos:
- 55 students across classes 1-5 (realistic Pakistani names, father names, phones)
- Monthly tuition fees for every student (mix of paid / partial / pending)
- Attendance for the last N school days (~90% attendance, realistic absences)
- Grades in 4 subjects per student (Math, English, Urdu, Science)

Built to survive slow/flaky connections (Vercel serverless cold starts,
Supabase latency): automatic retries with backoff, parallel workers, and
one failed request never crashes the whole run.

USAGE:
    python demo_data/seed_demo_data.py --url https://schoolhub-ivory.vercel.app --email YOUR_LOGIN_EMAIL --password YOUR_PASSWORD

Optional flags:
    --days 12       attendance days to seed (default 12; more days = longer runtime)
    --workers 8     parallel request workers (default 8)

TIP: Register a fresh school account first (e.g. "Demo Model School") and
seed THAT — keep demo data separate from any real school's account.

Safe to re-run: existing students (same class+roll) are skipped.
"""
import argparse
import random
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

random.seed(42)  # same data every run — predictable for demos

FIRST_NAMES_M = ["Ahmed", "Ali", "Hassan", "Hussain", "Bilal", "Usman", "Hamza", "Zain", "Ibrahim", "Abdullah",
                 "Umar", "Saad", "Taha", "Rayyan", "Musa", "Yusuf", "Danish", "Faizan", "Arham", "Shayan"]
FIRST_NAMES_F = ["Fatima", "Ayesha", "Zainab", "Maryam", "Khadija", "Amna", "Hira", "Iqra", "Mahnoor", "Zoya",
                 "Areeba", "Laiba", "Emaan", "Hania", "Rida", "Sana", "Noor", "Alishba", "Aleena", "Momina"]
LAST_NAMES = ["Khan", "Ahmed", "Malik", "Hussain", "Butt", "Chaudhry", "Sheikh", "Qureshi", "Awan", "Raza",
              "Baig", "Javed", "Iqbal", "Akhtar", "Nawaz", "Shahid", "Aslam", "Rafiq", "Saleem", "Tariq"]
FATHER_FIRST = ["Muhammad", "Abdul", "Ghulam", "Rana", "Malik", "Mirza", "Haji", "Syed", "Chaudhry", "Rao"]
FATHER_SECOND = ["Aslam", "Akram", "Rafiq", "Saleem", "Nawaz", "Shafiq", "Bashir", "Rasheed", "Younis", "Iqbal",
                 "Sadiq", "Latif", "Hanif", "Majeed", "Waheed"]

SUBJECTS = ["Mathematics", "English", "Urdu", "Science"]
CLASSES = ["1", "2", "3", "4", "5"]
STUDENTS_PER_CLASS = 11  # 5 classes x 11 = 55 students

MONTHLY_FEE = {"1": 1500, "2": 1500, "3": 1800, "4": 2000, "5": 2000}


def log(msg):
    print(msg, flush=True)


def make_session():
    """Session with automatic retries + backoff for flaky/slow connections."""
    session = requests.Session()
    retry = Retry(
        total=4,
        backoff_factor=2,          # waits 2s, 4s, 8s, 16s between retries
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=["GET", "POST"],
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def safe_post(session, url, json_body, headers, timeout=60):
    """POST that never raises — returns (status_code, json_or_None)."""
    for attempt in range(3):
        try:
            r = session.post(url, json=json_body, headers=headers, timeout=timeout)
            try:
                return r.status_code, r.json()
            except ValueError:
                return r.status_code, None
        except requests.RequestException:
            if attempt < 2:
                continue
            return 0, None  # network-level failure after all retries
    return 0, None


def make_students():
    students = []
    for class_name in CLASSES:
        for roll in range(1, STUDENTS_PER_CLASS + 1):
            gender = random.choice(["male", "female"])
            first = random.choice(FIRST_NAMES_M if gender == "male" else FIRST_NAMES_F)
            last = random.choice(LAST_NAMES)
            father = f"{random.choice(FATHER_FIRST)} {random.choice(FATHER_SECOND)}"
            phone = f"03{random.randint(0, 4)}{random.randint(10000000, 99999999)}"
            # ~20% siblings share the same phone as the previous student (family rollup demo)
            if students and random.random() < 0.2:
                phone = students[-1]["phone"]
                father = students[-1]["father_name"]
            students.append({
                "name": f"{first} {last}",
                "father_name": father,
                "class_name": class_name,
                "roll_number": str(roll),
                "phone": phone,
                "gender": gender,
                "date_of_birth": f"{2020 - int(class_name) - 5}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                "address": f"House {random.randint(1, 200)}, Street {random.randint(1, 20)}, Mohalla {random.choice(['Islampura', 'Madina Colony', 'Gulshan', 'Rehmat Abad', 'Farooq Gunj'])}",
            })
    return students


def school_days_back(n):
    """Last n weekdays (Mon-Sat, Sunday off) ending yesterday."""
    days = []
    d = date.today() - timedelta(days=1)
    while len(days) < n:
        if d.weekday() != 6:  # Sunday
            days.append(d)
        d -= timedelta(days=1)
    return list(reversed(days))


def run_parallel(tasks, workers, label):
    """tasks: list of zero-arg callables returning True/False. Shows progress."""
    done_ok = 0
    done_fail = 0
    total = len(tasks)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            if fut.result():
                done_ok += 1
            else:
                done_fail += 1
            if i % 50 == 0 or i == total:
                log(f"   {label}: {i}/{total} done ({done_fail} failed)")
    return done_ok, done_fail


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="e.g. https://schoolhub-ivory.vercel.app")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--days", type=int, default=12, help="attendance days to seed (default 12)")
    parser.add_argument("--workers", type=int, default=8, help="parallel workers (default 8)")
    args = parser.parse_args()
    base = args.url.rstrip("/")

    session = make_session()

    # Login (with generous timeout for serverless cold start)
    log("🔑 Logging in (first request may be slow — server waking up)...")
    status, data = safe_post(session, f"{base}/auth/login",
                             {"email": args.email, "password": args.password}, {}, timeout=90)
    if status != 200 or not data:
        log(f"❌ Login failed (status {status}). Check URL/email/password and try again.")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {data['access_token']}"}
    log(f"✅ Logged in as {args.email}")

    # ---- Students (sequential — order matters for sibling phone sharing; only 55) ----
    log("👨‍🎓 Creating students...")
    created_students = []
    skipped = 0
    failed = 0
    for s in make_students():
        status, resp = safe_post(session, f"{base}/students", s, headers)
        if status == 201 and resp:
            created_students.append(resp)
        elif status == 409:
            skipped += 1
        else:
            failed += 1
    log(f"✅ Students: {len(created_students)} created, {skipped} skipped (already existed), {failed} failed")

    # Always work from the FULL student list (covers partial previous runs where
    # some students were created earlier and would otherwise miss fees/grades).
    try:
        r = session.get(f"{base}/students", headers=headers, timeout=60)
        all_students = r.json() if r.status_code == 200 else created_students
    except requests.RequestException:
        all_students = created_students
    created_students = all_students

    if not created_students:
        log("❌ No students available — cannot seed fees/attendance/grades. Re-run the script.")
        sys.exit(1)

    # Fetch existing fees/grades so re-runs don't create duplicates.
    month_name = date.today().strftime("%B")
    students_with_fee = set()
    try:
        r = session.get(f"{base}/fees", headers=headers, timeout=60)
        if r.status_code == 200:
            for f in r.json():
                if f.get("fee_name") == "Tuition Fee" and f.get("month") == month_name:
                    students_with_fee.add(f["student_id"])
    except requests.RequestException:
        pass

    students_with_grades = set()
    try:
        r = session.get(f"{base}/grades", headers=headers, timeout=60)
        if r.status_code == 200:
            for g in r.json():
                students_with_grades.add(g["student_id"])
    except requests.RequestException:
        pass

    # ---- Fees (parallel) ----
    log("💰 Creating fees + payments...")
    fee_targets = [s for s in created_students if s["id"] not in students_with_fee]
    if len(fee_targets) < len(created_students):
        log(f"   (skipping {len(created_students) - len(fee_targets)} students who already have this month's fee)")

    def fee_task(s):
        amount = MONTHLY_FEE.get(s["class_name"], 1500)
        status, fee = safe_post(session, f"{base}/fees", {
            "student_id": s["id"], "fee_name": "Tuition Fee", "amount": amount,
            "month": month_name, "due_date": date.today().replace(day=10).isoformat(),
        }, headers)
        if status != 201 or not fee:
            return False
        roll = random.random()
        pay = amount if roll < 0.55 else (round(amount * random.choice([0.25, 0.5, 0.75])) if roll < 0.75 else 0)
        if pay > 0:
            safe_post(session, f"{base}/fees/{fee['id']}/payment",
                      {"fee_id": fee["id"], "amount_paid": pay, "payment_method": "cash"}, headers)
        return True

    ok, fail = run_parallel([lambda s=s: fee_task(s) for s in fee_targets], args.workers, "fees")
    log(f"✅ Fees: {ok} created ({fail} failed)")

    # ---- Attendance (parallel — the big one) ----
    days = school_days_back(args.days)
    log(f"📅 Creating attendance for {len(days)} school days x {len(created_students)} students = {len(days)*len(created_students)} records...")

    def attendance_task(sid, d):
        is_present = random.random() < 0.9
        status, _ = safe_post(session, f"{base}/attendance", {
            "student_id": sid, "date": d.isoformat(), "is_present": is_present,
            "remarks": None if is_present else random.choice([None, "Sick", "Family emergency", None]),
        }, headers)
        return status in (201, 409)  # 409 = already marked (re-run), counts as fine

    att_tasks = [lambda sid=s["id"], d=d: attendance_task(sid, d) for s in created_students for d in days]
    ok, fail = run_parallel(att_tasks, args.workers, "attendance")
    log(f"✅ Attendance: {ok} records ({fail} failed)")

    # ---- Grades (parallel) ----
    log("📊 Creating grades...")
    grade_targets = [s for s in created_students if s["id"] not in students_with_grades]
    if len(grade_targets) < len(created_students):
        log(f"   (skipping {len(created_students) - len(grade_targets)} students who already have grades)")

    def grade_task(sid, subject, ability):
        marks = round(min(100, max(20, random.gauss(ability * 100, 8))))
        status, _ = safe_post(session, f"{base}/grades", {
            "student_id": sid, "subject": subject,
            "marks_obtained": marks, "total_marks": 100,
            "exam_date": (date.today() - timedelta(days=random.randint(5, 25))).isoformat(),
        }, headers)
        return status == 201

    grade_tasks = []
    for s in grade_targets:
        ability = random.uniform(0.45, 0.95)
        for subject in SUBJECTS:
            grade_tasks.append(lambda sid=s["id"], sub=subject, ab=ability: grade_task(sid, sub, ab))
    ok, fail = run_parallel(grade_tasks, args.workers, "grades")
    log(f"✅ Grades: {ok} records ({fail} failed)")

    log("\n🎉 Demo data seeding complete! Open the dashboard and refresh.")
    log("   (Agar kuch records fail hue hon, script dobara chala dein — duplicates skip ho jayenge.)")


if __name__ == "__main__":
    main()