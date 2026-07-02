# School Hub — School Management System

A lightweight, WhatsApp-first school management system built for small private schools.
Backend: Python (FastAPI + SQLAlchemy + SQLite). Frontend: vanilla HTML/CSS/JS — no build step required.

---

## ✨ Features

**Core Management**
- Multi-tenant: each school registers its own account with isolated data
- Student records (with father's/mother's name, class, roll number, contact info)
- Staff management (teachers/admin/staff, salary payments)
- Attendance tracking, per date
- Grades/exam records per subject
- Fee management: create, edit, delete, record partial/full payments
- Announcements

**WhatsApp-first parent communication** (no paid API — uses `wa.me` links, tap to send)
- Fee reminders (pending & partial payments, with correct due amounts)
- Bulk "Remind All Unpaid" — one click lists every family with dues
- **Family/sibling rollup** — one combined message per guardian phone number instead of one per child
- **Same-day absence alerts** — notify parents the day a student is marked absent
- **Daily digest for the owner** — attendance %, fees collected today, outstanding dues, shareable in one tap
- Academic report share — subject-wise marks + attendance sent directly to a parent's WhatsApp

**Printable documents** (browser print → can be saved as PDF)
- Fee receipts
- Report cards
- Student ID cards
- Admission slips

**Reporting**
- Class-wise dues dashboard (total fee, collected, due, overdue count, collection rate per class)
- Student profile view (attendance rate, grade average, full fee history in one place)
- Bulk fee generation for an entire class in one action

---

## 🛠 Tech Stack

- **Backend:** FastAPI, SQLAlchemy 2.0, SQLite, JWT auth (PyJWT), Passlib/bcrypt for password hashing
- **Frontend:** Vanilla HTML/CSS/JS (single-file dashboard, no framework/build step)
- **Database:** SQLite (file-based, zero external DB server needed)

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- pip

### 1. Clone the repo
```bash
git clone https://github.com/sohail2365/schoolhub.git
cd schoolhub
```

### 2. Set up a virtual environment
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the backend
```bash
python -m backend.main
```
The API will be available at `http://127.0.0.1:8000`.
Interactive API docs: `http://127.0.0.1:8000/docs`

### 5. Open the app
The backend now serves the frontend too — just open:
```
http://127.0.0.1:8000/login.html
```
(No separate frontend server needed. This also means the exact same code works unchanged once deployed to a real domain — no URLs to edit.)

### 6. Create your school account
Use the registration page (`register.html`) to create your school, then log in with the admin credentials you set.

---

## 🌐 Going Live (24/7, accessible from any device)

Running on your own laptop only works while your laptop is on and connected.
Two deployment paths, depending on budget:

- **[VERCEL_DEPLOYMENT.md](./VERCEL_DEPLOYMENT.md)** — Free (Vercel + Supabase Postgres). Good for a first pilot client. Has real trade-offs (no automatic backups, free-tier project auto-pause after inactivity) — read the "Honest limitations" section first.
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** — Paid VPS (~PKR 2,000–3,000/month). No pause/backup trade-offs, better fit once you have paying clients.

---

## 📁 Project Structure

```
schoolhub/
├── backend/
│   ├── main.py               # FastAPI app entrypoint
│   ├── database.py           # SQLAlchemy engine/session setup
│   ├── models/                # SQLAlchemy models (Student, Fee, Staff, Grade, etc.)
│   ├── schemas/                # Pydantic request/response schemas
│   ├── routes/                # API routers (students, fees, attendance, grades, ...)
│   └── utils/                  # JWT handling, RBAC helpers
├── frontend/
│   ├── professional_dashboard.html   # Main app (single-file dashboard)
│   ├── login.html
│   ├── register.html
│   └── js/                      # Supporting JS modules
├── requirements.txt
└── school.db                    # SQLite database file (gitignored — not tracked)
```

---

## ⚠️ Important Notes

- **`school.db` is intentionally excluded from version control** (see `.gitignore`). It contains real student/parent data once you start using the app — never commit it to a public repository.
- **Before deploying for real clients**, run `python backend/generate_env.py` to generate a proper `.env` with a random JWT secret. The default secret shipped in the code is public (visible to anyone who reads the repo) and must never be used in production — see [DEPLOYMENT.md](./DEPLOYMENT.md).
- **Backups**: since this is multi-tenant (every school's data lives in one `school.db`), set up the automated backup cron job described in DEPLOYMENT.md before onboarding real paying clients — one file loss would affect everyone at once.
- WhatsApp messaging uses `wa.me` links (opens WhatsApp with a pre-filled message) — this requires manually tapping "Send" per contact since it doesn't use the paid WhatsApp Business API. This keeps the system free to run.

---

## 🗺 Roadmap

- Real payment gateway integration (JazzCash/EasyPaisa)
- WhatsApp Business API for fully automated sending (no manual tap-to-send)
- Teacher-to-class assignment (for teacher-wise reporting)
- Biometric/QR-based attendance

---

## 📄 License

Private project — all rights reserved unless otherwise stated by the project owner.
