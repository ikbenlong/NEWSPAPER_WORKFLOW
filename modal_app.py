"""
Le Financial NewsPaper — Modal scheduled app.
Runs every Monday at 08:00 UTC.

Setup (one-time):
  pip install modal
  modal token new
  modal secret create newsletter-secrets \
    ANTHROPIC_API_KEY=... \
    PERPLEXITY_API_KEY=... \
    GMAIL_SENDER=... \
    GMAIL_APP_PASSWORD=... \
    NEWSLETTER_RECIPIENT=...

Deploy:
  modal deploy modal_app.py

Run immediately:
  modal run modal_app.py
"""

import sys
import modal

app = modal.App("le-financial-newspaper")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "anthropic>=0.25.0",
        "python-dotenv>=1.0.0",
        "requests>=2.31.0",
    )
)

tools_mount = modal.Mount.from_local_dir("tools", remote_path="/app/tools")
logo_mount  = modal.Mount.from_local_dir("Logo",  remote_path="/app/Logo")


@app.function(
    image=image,
    schedule=modal.Cron("0 8 * * 1"),  # Every Monday at 08:00 UTC
    secrets=[modal.Secret.from_name("newsletter-secrets")],
    mounts=[tools_mount, logo_mount],
    timeout=300,
)
def send_weekly_newsletter():
    sys.path.insert(0, "/app/tools")

    from research_topic   import research_topic
    from write_newsletter import write_newsletter
    from format_html      import format_html
    from send_email       import send_email

    topic = "Gold Price Silver Price EUR/USD EUR/GBP weekly market analysis"

    print("► 1/4  Researching last 7 days...")
    research = research_topic(topic)

    print("► 2/4  Writing newsletter...")
    newsletter = write_newsletter(research, topic)

    print("► 3/4  Formatting HTML...")
    html = format_html(newsletter)

    subject = newsletter.get("subject_line", "Weekly Markets Report")
    print(f"► 4/4  Sending: {subject!r}")
    result = send_email(html, subject)

    print(f"✓ {result['message']} → {', '.join(result['recipients'])}")
    return result


@app.local_entrypoint()
def main():
    """Trigger the newsletter immediately: modal run modal_app.py"""
    send_weekly_newsletter.remote()
