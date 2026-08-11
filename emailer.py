"""
Sends the report-ready email via Resend, the same provider CMC Connect
already uses. Runs in stub mode (logs instead of sending) until
RESEND_API_KEY is set as an environment variable.
"""
import os
import requests

RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "reports@yourclinic.com")
PORTAL_BASE_URL = os.environ.get("PORTAL_BASE_URL", "http://127.0.0.1:8000/portal")


def send_report_ready_email(lead):
    signup_url = f"{PORTAL_BASE_URL}/signup.html?lead_id={lead.id}"

    subject = "Your Women's Health Check is ready"
    html = f"""
    <div style="font-family:Arial,sans-serif; max-width:520px; margin:0 auto; color:#241933;">
      <h2 style="color:#2E0854;">Your results are ready</h2>
      <p>Hi{f' {lead.name}' if lead.name else ''},</p>
      <p>Thanks for completing your Women's Health Check. Your full personalised report,
      with next steps and a specialist recommendation, is ready to view.</p>
      <p style="margin:24px 0;">
        <a href="{signup_url}" style="background:#C9A227; color:#2E0854; padding:14px 24px;
        border-radius:100px; text-decoration:none; font-weight:bold; display:inline-block;">
          View my full report
        </a>
      </p>
      <p style="font-size:13px; color:#5B4E6D;">
        Can't see this email in your inbox? It's worth checking your spam or junk folder,
        first emails from a new sender often land there by mistake.
      </p>
      <p style="font-size:13px; color:#5B4E6D;">
        This report is for informational purposes and does not replace medical advice.
      </p>
    </div>
    """

    if not RESEND_API_KEY:
        print(f"[email stub] Would send report-ready email to {lead.email} -> {signup_url}")
        return {"stub": True, "signup_url": signup_url}

    response = requests.post(
        "https://api.resend.com/emails",
        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
        json={"from": EMAIL_FROM, "to": [lead.email], "subject": subject, "html": html},
        timeout=10,
    )
    response.raise_for_status()
    return response.json()
