"""
Gmail SMTP client for sending digest/alert emails.

Uses Gmail App Password (not your main password).
Create one at: https://myaccount.google.com/apppasswords

Set in your server .env:
  GMAIL_USER         — your Gmail address
  GMAIL_APP_PASSWORD — the 16-character app password
  ALERT_EMAIL        — where to send reports (can be same as GMAIL_USER)
"""
from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional


def send_email(
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
    to: Optional[str] = None,
) -> bool:
    """
    Send an email via Gmail SMTP.
    Returns True on success, False on failure (never raises).
    """
    gmail_user = os.getenv("GMAIL_USER", "").strip()
    app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
    recipient = to or os.getenv("ALERT_EMAIL", gmail_user).strip()

    if not gmail_user or not app_password or not recipient:
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"ProfitEngine <{gmail_user}>"
    msg["To"] = recipient

    if body_text:
        msg.attach(MIMEText(body_text, "plain"))
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(gmail_user, app_password)
            server.sendmail(gmail_user, recipient, msg.as_string())
        return True
    except Exception:
        return False


def send_publish_digest(published_articles: list, cycle_metrics: dict) -> bool:
    """
    Send a formatted digest of articles published in this cycle.
    published_articles: list of dicts with 'title', 'url', 'platform'
    """
    if not published_articles:
        return False

    rows = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>"
        f"<a href='{a.get('url','#')}'>{a.get('title','Untitled')}</a></td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;color:#666'>"
        f"{a.get('platform','')}</td></tr>"
        for a in published_articles
    )

    body_html = f"""
    <html><body style='font-family:sans-serif;color:#333;max-width:600px;margin:auto'>
    <h2 style='color:#00aa55'>ProfitEngine — Content Published ✅</h2>
    <p><strong>{len(published_articles)}</strong> article(s) published this cycle.</p>
    <table style='width:100%;border-collapse:collapse'>
      <thead><tr>
        <th style='text-align:left;padding:8px;background:#f5f5f5'>Article</th>
        <th style='text-align:left;padding:8px;background:#f5f5f5'>Platform</th>
      </tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p style='color:#999;font-size:12px;margin-top:24px'>
      Total cycles: {cycle_metrics.get('total_cycles', 0)} ·
      Success rate: {cycle_metrics.get('success_rate_pct', 0)}%
    </p>
    </body></html>
    """

    return send_email(
        subject=f"ProfitEngine: {len(published_articles)} article(s) published",
        body_html=body_html,
        body_text=f"Published {len(published_articles)} articles: "
        + ", ".join(a.get("title", "") for a in published_articles),
    )
