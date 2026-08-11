# Women's Health Check: Backend

FastAPI backend for the Women's Health Check quiz. Handles lead
storage, server-side scoring, the practitioner review queue, account
signup, PDF report downloads, the report-ready email, and WhatsApp
community click tracking.

## How the full flow works now

1. Someone completes the quiz. The front end posts their answers to
   `POST /api/leads`. The backend scores the answers server-side and
   stores the lead as `pending_review`.
2. The backend immediately sends a **report-ready email** (via
   `emailer.py`). This email never contains the detailed report
   itself, only a teaser-free "your results are ready" message and a
   link to `/portal/signup.html?lead_id=...`. Nothing sensitive
   travels by email.
3. The email explicitly tells people to check spam/junk, since first
   emails from a new sender routinely land there.
4. They land on the signup page, enter name, email, phone, and a free
   bio field, plus a password, and get an account (`POST
   /api/signup`), linked back to their original lead via `lead_id`.
5. Logged into `/portal/account.html`, they see their report status
   (`pending_review` or `reviewed`), a summary of each track, a button
   to download the full report as a PDF, and a button to join your
   WhatsApp community.
6. A practitioner still reviews the report independently via `/admin`,
   whenever they get to it. The account page shows the current status
   plainly either way, so nothing is hidden, just not gated behind
   waiting for review before the person can see anything at all.

## What's stubbed, on purpose, for this first pass

- **Email sending**: works in "stub mode" (logs instead of sending)
  until you set `RESEND_API_KEY`. Once set, `emailer.py` sends for
  real via Resend, same provider CMC Connect already uses.
- **WhatsApp**: this is a static community invite link
  (`WHATSAPP_COMMUNITY_URL`), not a bot integration. A real
  account-linked WhatsApp bot needs Meta's WhatsApp Business API,
  which requires business verification and approval, a separate,
  heavier project if you want it later. For now, clicking "Join our
  WhatsApp community" opens your invite link and is tracked
  server-side so you know who clicked.
- **Practitioner auth**: still one shared API key, not individual
  logins. Fine for a single-practitioner pilot.

## Running it locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

Then visit:
- `http://localhost:8000/docs` to test the API directly
- `http://localhost:8000/admin` for the practitioner review queue
- `http://localhost:8000/portal/signup.html?lead_id=<id>` to test
  signup (grab a real `lead_id` from a test submission via `/docs`
  first)
- `http://localhost:8000/portal/account.html` after signing up or
  logging in

## Deploying to Render

Same as before, push to GitHub, connect the repo in Render, set the
environment variables. New ones to set for this pass:

- `JWT_SECRET` change this from the placeholder, it signs login tokens
- `RESEND_API_KEY` and `EMAIL_FROM` once you're ready for real emails to send
- `PORTAL_BASE_URL` defaults to this backend's own `/portal` path, which works with no separate hosting needed
- `WHATSAPP_COMMUNITY_URL` your actual WhatsApp community invite link

## Connecting the quiz front end

Already done, `womens-health-quiz.html` now posts to `POST
/api/leads` on submission and shows a "check your inbox, including
spam" confirmation instead of the full report.
