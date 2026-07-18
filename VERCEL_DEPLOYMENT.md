# Deploying to Vercel + Supabase (Free)

This is the **free** deployment path. Read the "Honest limitations" section
before committing to this for a real paying client — free isn't free of
trade-offs.

---

## ⚠️ Honest limitations of this path (read first)

1. **Supabase free tier has NO automatic backups.** If data is lost/corrupted,
   there's no built-in recovery. You must back up manually (covered below).
2. **Supabase free projects pause after 7 days of inactivity.** If nobody
   uses the app for a week, it goes offline until someone manually clicks
   "Resume" in the Supabase dashboard. Mitigated below with a free uptime
   pinger, but worth knowing.
3. **500MB database storage limit.** Plenty for a single small school for a
   long time — just know it exists.
4. **Vercel serverless cold starts.** First request after inactivity may take
   1-3 seconds. Not a problem for normal use.

None of these are dealbreakers for a pilot/first client, but factor them into
your pricing conversation once a client is actually paying — a $25/month
Supabase Pro plan (or a small VPS) removes all four once you have paying
clients who'd notice downtime.

---

## 1. Create a Supabase project (free Postgres database)

1. Go to **supabase.com** → Sign up → **New Project**
2. Pick a name, set a strong database password (save it — you'll need it)
3. Pick a region close to Pakistan (Singapore is usually closest)
4. Wait ~2 minutes for provisioning

### Get your connection string

Project Settings → Database → Connection String → **URI** (choose "Session pooler" or "Transaction pooler" mode — NOT direct connection, since Vercel serverless functions need pooled connections).

It looks like:
```
postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

You'll paste this into Vercel as `DATABASE_URL`, but change the prefix from
`postgresql://` to `postgresql+psycopg2://` (SQLAlchemy needs the driver
specified explicitly):
```
postgresql+psycopg2://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

---

## 2. Generate a real JWT secret (do this locally, once)

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output — you'll paste it into Vercel as `JWT_SECRET` in the next step.

---

## 3. Deploy to Vercel

1. Push your code to GitHub (already done — `sohail2365/schoolhub`)
2. Go to **vercel.com** → **Add New Project** → Import `sohail2365/schoolhub`
3. Framework Preset: **Other**
4. Root Directory: leave empty (project root)
5. Before deploying, add **Environment Variables**:

| Key | Value |
|---|---|
| `DATABASE_URL` | Your Supabase connection string (with `+psycopg2`, from step 1) |
| `JWT_SECRET` | The random secret you generated in step 2 |
| `DEBUG` | `False` |
| `CORS_ORIGINS` | `*` |

**Optional — for password reset emails to actually send** (otherwise reset links only show up in Vercel's function logs, which isn't useful for real users):

| Key | Value |
|---|---|
| `SMTP_HOST` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SMTP_USER` | Your Gmail address |
| `SMTP_PASSWORD` | A Gmail [App Password](https://myaccount.google.com/apppasswords) (not your normal Gmail password) |
| `SMTP_FROM_EMAIL` | Same as `SMTP_USER` |
| `FRONTEND_BASE_URL` | Your live URL, e.g. `https://schoolhub-ivory.vercel.app` (used to build the reset link in the email) |

**Optional — for the Super Admin panel** (platform owner access to see/deactivate/delete any school's account):

| Key | Value |
|---|---|
| `SUPER_ADMIN_SECRET` | A long random value — generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Keep this private; anyone with it can manage every school on your platform. |

Access it at `https://your-app.vercel.app/superadmin.html` (not linked from anywhere in the normal app — bookmark it).

**Optional — for AI features** (student summaries & class reports):

| Key | Value |
|---|---|
| `GROQ_API_KEY` | Free API key from [console.groq.com](https://console.groq.com) |

Without this, the AI buttons show a clear "not configured" message and everything else works normally. Note: AI features send student data (names, grades, attendance, fee totals) to Groq's API to generate summaries — mention this to schools if they ask about data privacy.

6. Click **Deploy**

Vercel will build and give you a live URL like `https://schoolhub.vercel.app`.
Visit `https://schoolhub.vercel.app/login.html` — the app should load, and
the database tables get created automatically on first request (same
non-destructive migration logic as local dev).

---

## 4. Set up a free uptime pinger (prevents Supabase auto-pause)

1. Sign up at **uptimerobot.com** (free tier: 50 monitors, 5-minute intervals)
2. Add New Monitor → HTTP(s) → URL: `https://your-app.vercel.app/keep-alive`
3. Set interval to every 3 days (comfortably under Supabase's 7-day pause threshold)

This endpoint runs a trivial database query, which counts as activity and
keeps the Supabase project from pausing.

---

## 5. Set up manual backups (since free tier has none built-in)

**Simplest approach — from your own computer, periodically:**

```bash
# Install the Supabase CLI once: https://supabase.com/docs/guides/cli
supabase db dump --db-url "postgresql://postgres:[PASSWORD]@[YOUR-HOST]:5432/postgres" > backup_$(date +%Y-%m-%d).sql
```

Run this weekly (or after anything major, like onboarding a new client) and
keep the `.sql` files somewhere safe (your own laptop, Google Drive, etc.).
`backend/backup_db.py` from the VPS guide is SQLite-specific and doesn't
apply here — this manual dump is the equivalent for Postgres.

**More automated option (if you want it later):** a GitHub Actions scheduled
workflow that runs `supabase db dump` on a cron schedule and uploads the
result as an artifact — free, but more setup than this guide covers. Worth
doing once you have real paying clients.

---

## 6. Updating the app later

Push to GitHub `main` → Vercel auto-deploys on every push (already connected
via the GitHub import in step 3). No manual redeploy steps needed.

---

## When to move off this free path

Move to a paid VPS (see `DEPLOYMENT.md`) or Supabase Pro once:
- You have a paying client who'd be upset by a week-long pause after a school holiday
- You're near the 500MB storage limit
- You want automatic backups without remembering to run one manually
