#!/usr/bin/env python3
"""Send Medium API access request email via Resend (verified domain alreadyherellc.com).

Falls back to Gmail SMTP only if RESEND_API_KEY is absent. Resend is preferred because
the Gmail app password was revoked; alreadyherellc.com is a verified Resend sender domain.
"""
import json
import os
import urllib.request

RECIPIENT = "yourfriends@medium.com"
SUBJECT = "API Access Request - ProfitEngine v5 / Already Here LLC"
SENDER = "Stephen - Already Here LLC <dispatch@alreadyherellc.com>"

body = (
    "Hi Medium team,\n\n"
    "My name is Stephen, founder of Already Here LLC. I am building ProfitEngine v5, "
    "an automated content publishing platform that helps small business owners and indie "
    "builders create and distribute SEO-optimized articles across multiple platforms.\n\n"
    "We would like to integrate Medium's API to publish our generated content directly to "
    "our Medium publication. We are currently live on GitHub Pages, Dev.to, and Hashnode. "
    "Medium is the final distribution channel we want to activate.\n\n"
    "Details:\n"
    "- Company: Already Here LLC\n"
    "- Website: https://app.alreadyherellc.com\n"
    "- Use case: Automated cross-posting of original long-form articles (1,000-1,500 words) "
    "on AI tools, passive income, and developer productivity\n"
    "- Scopes needed: basicProfile, publishPost\n"
    "- Publishing frequency: 1-3 articles per day\n"
    "- Contact email: dispatch@alreadyherellc.com\n\n"
    "We publish original content with proper FTC disclosures and canonical URLs. "
    "All articles are written by our AI pipeline using Groq/Gemini with human editorial oversight.\n\n"
    "Would you be able to grant us a clientId and clientSecret, or confirm whether a "
    "self-issued integration token from Settings > Integration Tokens covers the publishPost "
    "scope for our account?\n\n"
    "Thank you for your time.\n\n"
    "Best,\n"
    "Stephen\n"
    "Already Here LLC\n"
    "dispatch@alreadyherellc.com\n"
    "https://app.alreadyherellc.com"
)


def send_via_resend(api_key: str, recipient: str = RECIPIENT) -> None:
    payload = json.dumps({
        "from": SENDER,
        "to": [recipient],
        "reply_to": "dispatch@alreadyherellc.com",
        "subject": SUBJECT,
        "text": body,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "already-here-llc-mailer/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise SystemExit(f"Resend rejected the send (HTTP {exc.code}): {detail}")
    print(f"SUCCESS: Email sent to {recipient} via Resend (id={result.get('id')})")


def send_via_gmail(user: str, app_password: str) -> None:
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = f"Stephen - Already Here LLC <{user}>"
    msg["To"] = RECIPIENT
    msg["Reply-To"] = "dispatch@alreadyherellc.com"
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(user, app_password)
        server.sendmail(user, RECIPIENT, msg.as_string())
    print(f"SUCCESS: Email sent to {RECIPIENT} via Gmail")


def main() -> None:
    resend_key = os.environ.get("RESEND_API_KEY", "").strip()
    override = os.environ.get("TEST_RECIPIENT", "").strip()
    if resend_key:
        send_via_resend(resend_key, override or RECIPIENT)
        return
    gmail_user = os.environ.get("GMAIL_USER", "alreadyherellc@gmail.com")
    app_password = os.environ.get("GMAIL_APP_PASSWORD", "").strip()
    if not app_password:
        raise SystemExit("Neither RESEND_API_KEY nor GMAIL_APP_PASSWORD is set")
    send_via_gmail(gmail_user, app_password)


if __name__ == "__main__":
    main()
