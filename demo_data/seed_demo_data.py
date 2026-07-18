"""
Demo Data Seeder for SchoolHub
==============================

Fills a school account with realistic demo data for client demos:
- 55 students across classes 1-5 (realistic Pakistani names, father names, phones)
- Monthly tuition fees for every student (mix of paid / partial / pending)
- Attendance for the last 20 school days (~90% attendance, realistic absences)
- Grades in 4 subjects per student (Math, English, Urdu, Science)

It seeds through the normal REST API (not direct DB access), so it works
against BOTH a local server and the deployed Vercel app.

USAGE:
    python demo_data/seed_demo_data.py --url https://schoolhub-ivory.vercel.app --email YOUR_LOGIN_EMAIL --password YOUR_PASSWORD

    (or for local testing:)
    python demo_data/seed_demo_data.py --url http://127.0.0.1:8000 --email ... --password ...

TIP: Register a fresh school account first (e.g. "Demo Model School") and
seed THAT — keep demo data separate from any real school's account.

NOTE: Running twice will skip students that already exist (duplicate roll
numbers are rejected by the API), so it's safe to re-run.
"""
import argparse
import random
import sys
from datetime import date, timedelta

import requests

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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", required=True, help="e.g. https://schoolhub-ivory.vercel.app")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    base = args.url.rstrip("/")

    # Login
    r = requests.post(f"{base}/auth/login", json={"email": args.email, "password": args.password}, timeout=30)
    if r.status_code != 200:
        log(f"❌ Login failed ({r.status_code}): {r.text[:200]}")
        sys.exit(1)
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    log(f"✅ Logged in as {args.email}")

    # ---- Students ----
    created_students = []
    skipped = 0
    for s in make_students():
        r = requests.post(f"{base}/students", json=s, headers=headers, timeout=30)
        if r.status_code == 201:
            created_students.append(r.json())
        elif r.status_code == 409:
            skipped += 1
        else:
            log(f"⚠️  Student '{s['name']}' failed ({r.status_code}): {r.text[:150]}")
    log(f"✅ Students: {len(created_students)} created, {skipped} skipped (already existed)")

    if not created_students:
        # Re-fetch existing students so fees/attendance/grades can still be seeded on re-runs
        r = requests.get(f"{base}/students", headers=headers, timeout=30)
        created_students = r.json() if r.status_code == 200 else []
        log(f"ℹ️  Using {len(created_students)} existing students for remaining data")

    # ---- Fees (current month tuition per student, mixed statuses) ----
    month_name = date.today().strftime("%B")
    fees_created = 0
    payments_made = 0
    for s in created_students:
        amount = MONTHLY_FEE.get(s["class_name"], 1500)
        r = requests.post(f"{base}/fees", json={
            "student_id": s["id"], "fee_name": "Tuition Fee", "amount": amount,
            "month": month_name,
            "due_date": date.today().replace(day=10).isoformat(),
        }, headers=headers, timeout=30)
        if r.status_code != 201:
            continue
        fees_created += 1
        fee = r.json()

        roll = random.random()
        if roll < 0.55:        # 55% fully paid
            pay = amount
        elif roll < 0.75:      # 20% partially paid
            pay = round(amount * random.choice([0.25, 0.5, 0.75]))
        else:                  # 25% unpaid
            pay = 0

        if pay > 0:
            pr = requests.post(f"{base}/fees/{fee['id']}/payment", json={
                "fee_id": fee["id"], "amount_paid": pay, "payment_method": "cash",
            }, headers=headers, timeout=30)
            if pr.status_code == 201:
                payments_made += 1
    log(f"✅ Fees: {fees_created} created, {payments_made} payments recorded (mix of paid/partial/pending)")

    # ---- Attendance (last 20 school days, ~90% present) ----
    days = school_days_back(20)
    attendance_created = 0
    for s in created_students:
        for d in days:
            is_present = random.random() < 0.9
            r = requests.post(f"{base}/attendance", json={
                "student_id": s["id"], "date": d.isoformat(), "is_present": is_present,
                "remarks": None if is_present else random.choice([None, "Sick", "Family emergency", None]),
            }, headers=headers, timeout=30)
            if r.status_code == 201:
                attendance_created += 1
    log(f"✅ Attendance: {attendance_created} records across {len(days)} school days")

    # ---- Grades (4 subjects each, realistic spread) ----
    grades_created = 0
    for s in created_students:
        ability = random.uniform(0.45, 0.95)  # each student has a consistent ability level
        for subject in SUBJECTS:
            marks = round(min(100, max(20, random.gauss(ability * 100, 8))))
            r = requests.post(f"{base}/grades", json={
                "student_id": s["id"], "subject": subject,
                "marks_obtained": marks, "total_marks": 100,
                "exam_date": (date.today() - timedelta(days=random.randint(5, 25))).isoformat(),
            }, headers=headers, timeout=30)
            if r.status_code == 201:
                grades_created += 1
    log(f"✅ Grades: {grades_created} records ({len(SUBJECTS)} subjects per student)")

    log("\n🎉 Demo data seeding complete! Open the dashboard and refresh.")


if __name__ == "__main__":
    main()
