#!/usr/bin/env python3
"""
Master script: research → write → format → send
Usage: python run_newsletter.py --topic "Gold Silver EUR/USD EUR/GBP"
"""
import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'), override=True)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'tools'))

from research_topic import research_topic
from write_newsletter import write_newsletter
from format_html import format_html
from send_email import send_email


def run(topic: str, recipients: list = None, style: str = "professional", dry_run: bool = False):
    print(f"\n{'='*60}")
    print(f"  Weekly Newsletter Pipeline")
    print(f"  Topic: {topic}")
    print(f"{'='*60}\n")

    # Step 1: Research
    print("► Step 1/4: Researching last 7 days...")
    research = research_topic(topic)

    # Step 2: Write
    print("\n► Step 2/4: Writing newsletter...")
    newsletter = write_newsletter(research, topic, style)

    # Step 3: Format
    print("\n► Step 3/4: Formatting HTML...")
    html = format_html(newsletter)

    # Step 4: Send
    subject = newsletter.get("subject_line", "Weekly Markets Report")
    if dry_run:
        print(f"\n► Step 4/4: DRY RUN — skipping send. Subject: {subject!r}")
    else:
        print(f"\n► Step 4/4: Sending: {subject!r}")
        result = send_email(html, subject, recipients)
        print(f"  ✓ {result['message']} → {', '.join(result['recipients'])}")

    print(f"\n{'='*60}")
    print("  Pipeline complete.")
    print(f"{'='*60}\n")
    return newsletter


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full newsletter pipeline")
    parser.add_argument("--topic", default="Gold Price Silver Price EUR/USD EUR/GBP weekly market analysis",
                        help="Market topic to cover")
    parser.add_argument("--recipients", help="Comma-separated recipient emails (overrides .env default)")
    parser.add_argument("--style", default="professional", choices=["professional", "casual", "technical"])
    parser.add_argument("--dry-run", action="store_true", help="Skip sending the email")
    args = parser.parse_args()

    recipients = [r.strip() for r in args.recipients.split(",")] if args.recipients else None
    run(args.topic, recipients, args.style, args.dry_run)
