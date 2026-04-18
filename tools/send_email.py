import argparse
import os
import re
import smtplib
import uuid
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

SENDER_NAME = "Le Financial NewsPaper"


def get_env(key):
    val = os.getenv(key)
    if not val or not val.strip():
        raise ValueError(f"Missing env var: {key}")
    return val.strip()


def _strip_html(html: str) -> str:
    text = re.sub(r'<[^>]+>', ' ', html)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    return text.strip()


def send_email(
    html_content: str,
    subject: str,
    recipients: list = None,
    sender: str = None,
) -> dict:
    sender_addr = sender or get_env('GMAIL_SENDER')
    app_password = get_env('GMAIL_APP_PASSWORD')

    if not recipients:
        default = os.getenv('NEWSLETTER_RECIPIENT', '').strip()
        if not default:
            raise ValueError("No recipients provided and NEWSLETTER_RECIPIENT not set in .env")
        recipients = [default]

    sender_domain = sender_addr.split('@')[-1]
    from_field = f"{SENDER_NAME} <{sender_addr}>"

    msg = MIMEMultipart("alternative")
    msg["Subject"]          = subject
    msg["From"]             = from_field
    msg["To"]               = ", ".join(recipients)
    msg["Date"]             = formatdate(localtime=True)
    msg["Message-ID"]       = make_msgid(domain=sender_domain)
    msg["Precedence"]       = "list"
    msg["List-Unsubscribe"] = f"<mailto:{sender_addr}?subject=unsubscribe>"
    msg["X-Mailer"]         = "Le Financial NewsPaper Automation"

    plain_text = _strip_html(html_content)
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    print(f"[send_email] Connecting to smtp.gmail.com:587...")
    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender_addr, app_password)
        server.sendmail(sender_addr, recipients, msg.as_string())

    print(f"[send_email] Sent '{subject}' → {', '.join(recipients)}")
    return {"success": True, "message": "Email sent", "recipients": recipients}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send HTML email via Gmail SMTP")
    parser.add_argument("--html", help="Path to HTML file")
    parser.add_argument("--subject", required=True, help="Email subject line")
    parser.add_argument("--recipients", help="Comma-separated recipient emails")
    args = parser.parse_args()

    if args.html:
        with open(args.html) as f:
            html_content = f.read()
    else:
        parser.error("Provide --html")

    recipients = [r.strip() for r in args.recipients.split(",")] if args.recipients else None
    result = send_email(html_content, args.subject, recipients)
    print(result)
