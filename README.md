# Women's Health Check: Backend

FastAPI backend for the Women's Health Check quiz. Handles lead
storage, server-side scoring, the practitioner review queue, and the
report send step.

## What this does right now

- **Receives quiz submissions** (`POST /api/leads`) and stores them,
  along with a server-computed report. Scoring is recalculated here,
  not trusted from the front end, so the numbers can't be tampered
  with in the browser.
- **Gives practitioners a review queue** at `/admin`, a lightweight
  page that lists everyone waiting for review, shows their report,
  and lets a practitioner approve it with optional notes.
- **Tracks the report lifecycle**: `pending_review` -> `reviewed` ->
  `sent`.
- **Tracks booking clicks** (`POST /api/leads/{id}/book-click`) so you
  can see how many people who got a report went on to click through
  to book.

## What's stubbed, on purpose, for this first pass

- **Email sending**: `send_report_email()` in `main.py` currently just
  logs instead of sending. Once you have a Resend API key (the same
  provider CMC Connect already uses) and a report email template,
  fill in the commented-out block.
- **Booking**: the click is tracked, but there's no real calendar
  integration yet. Simplest next step is a Calendly link per clinic,
  passed to the front end as a config value, rather than a full API
  integration.
- **Practitioner auth**: one shared API key (`PRACTITIONER_API_KEY`),
  not individual logins. Fine for a single-practitioner pilot. Once
  you have more than one practitioner or clinic, swap this for proper
  per-user auth, Clerk is the natural fit since CMC Connect already
  uses it.
- **Front-end connection**: the quiz HTML file built earlier still
  computes and shows the report entirely client-side and doesn't call
  this API yet. Wiring the quiz's "finish" step to `POST /api/leads`
  is the next piece of work, see below.

## Running it locally

```
pip install -r requirements.txt
uvicorn main:app --reload
```

This will create a local `womens_health.db` SQLite file automatically,
no database setup needed to test it. Visit `http://localhost:8000/admin`
for the review queue, and `http://localhost:8000/docs` for interactive
API docs.

## Deploying to Render

1. Push this folder to a GitHub repo (or a subfolder of `vantara`, if
   you'd rather keep it in the same repo as CMC Connect).
2. In Render, create a new Web Service from that repo. It will pick up
   `render.yaml` automatically.
3. Set the environment variables listed in `.env.example`, in
   particular `DATABASE_URL` (point this at a Supabase Postgres
   instance, same pattern as CMC Connect) and `PRACTITIONER_API_KEY`.
4. Once deployed, the review queue is at `https://<your-render-url>/admin`.

## Connecting the quiz front end

The quiz HTML file currently ends the flow by showing the report
directly in the browser. To connect it to this backend, add a `fetch`
call in its `showReport()` function that posts to
`POST /api/leads` with the person's name, email, consent choices,
`life_stage`, and `answers`. The response includes the server-computed
report, which can replace the client-side one shown on screen.

That also means adding an email capture step to the quiz itself, since
right now it never asks for one. Worth deciding whether that sits
before the report (gate the results behind an email) or after (show
the report first, then offer to email a copy), that's a product
decision rather than a technical one.
