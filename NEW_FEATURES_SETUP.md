# New Features Added

## 1. Setup required BEFORE these features work: Supabase Storage

Vercel's filesystem is ephemeral — a file saved to local disk during one
request is **gone** on the next request/deployment. So all image uploads
(ID card, B-form, test paper, card photo) go to **Supabase Storage**
instead, using the same Supabase project you already use for the database.

**Steps:**
1. Supabase dashboard → **Project Settings → API**. Copy:
   - `Project URL` → set as `SUPABASE_URL`
   - `service_role` secret key (NOT the `anon` key) → set as `SUPABASE_SERVICE_KEY`
2. Supabase dashboard → **Storage → New bucket** → name it exactly `student-files`
   → leave it **private** (do not enable "Public bucket"). B-forms/CNIC are
   sensitive ID documents, so files are served via 1-hour signed links, not
   permanent public URLs.
3. Add both env vars to Vercel (Project Settings → Environment Variables)
   and to your local `.env`.

Until these are set, upload endpoints return a clean "not configured" error
— nothing else breaks.

## 2. Student documents & photos (items 1 & 3)

New table `student_documents`. Each student can have multiple uploaded
files, tagged by type: `id_card`, `b_form`, `test_paper`, `profile_photo`, `other`.

- `POST /students/{id}/documents?doc_type=...&label=...` (multipart `file`) — upload
- `GET /students/{id}/documents` — list (metadata only, no direct file link)
- `GET /students/{id}/documents/{doc_id}/url` — get a fresh 1-hour signed link
- `DELETE /students/{id}/documents/{doc_id}` — admin only

Uploading with `doc_type=profile_photo` also sets `Student.photo_url`, so it
automatically becomes the photo used on the printable student ID card.

**Admin UI:** `frontend/student-documents.html` — pick a class → student →
upload/view/delete. Link to it from the dashboard, e.g.:
`<a href="student-documents.html">Student Documents</a>`

## 3. Monthly/annual test records with photo (item 2)

New table `test_records` — separate from the existing `Grade` table, tracks
`term_type` (monthly/annual), `period` (`"2026-07"` or `"2026"`), marks, and
an optional photo of the physical answer sheet.

- `POST /test-records` (multipart form: student_id, term_type, period, subject,
  marks_obtained, total_marks, remarks, optional `image` file)
- `GET /test-records?student_id=&class=&term_type=&period=`
- `GET /test-records/{id}/image-url` — signed link to the photo
- `PUT / DELETE /test-records/{id}`

Teachers can also add these for their own class only via
`POST /teacher/test-records` (see below).

## 4. Teacher Portal (item 4)

Previously only school admins could log in. Now:

**Admin creates teacher access:**
`POST /staff/{staff_id}/create-login` (staff record needs an email + a
`class_assigned` set). Returns a one-time temporary password — share it
with the teacher directly (WhatsApp/in person). Calling it again resets
the password instead of duplicating the account.

**Teacher logs in at** `frontend/teacher-login.html` → redirects to
`frontend/teacher-dashboard.html`.

**What a teacher can do (scoped strictly to their own assigned class —
enforced server-side, not just hidden in the UI):**
- View their class roster
- Mark attendance (`GET/POST /teacher/attendance`)
- Enter grades (`GET/POST /teacher/grades`)
- Add monthly/annual test records with photo (`GET/POST /teacher/test-records`)

A teacher cannot see or modify another class's students — every teacher
route checks `student.class_name == staff.class_assigned` before allowing
the write, so even a manipulated request from dev tools is rejected with
403.

## Migration notes

All new columns (`students.photo_url`, `staff.user_id`) are added
automatically on startup via the existing non-destructive `_ensure_column`
migration helper — no manual `ALTER TABLE` needed, matches how this project
already handles schema changes.

## Not done in this pass (flagging honestly)

- The main admin dashboard (`professional_dashboard.html`, 4000+ lines) was
  **not** edited to embed upload buttons inline — too risky to hand-edit
  blind without full context of its existing state management. The
  standalone `student-documents.html` page covers the same functionality
  safely. Wiring it into the main dashboard's UI is a good next step once
  you've tested this in isolation.
- No automated tests added for the new routes (existing project has a
  `backend/tests/` folder with 3 test files — worth extending later).
