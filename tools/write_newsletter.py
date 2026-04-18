import argparse
import json
import os
import re
from datetime import datetime, timedelta

import anthropic
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)


def get_env(key):
    val = os.getenv(key)
    if not val or not val.strip():
        raise ValueError(f"Missing env var: {key}")
    return val.strip()


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower())[:40].strip('_')


def write_newsletter(research: dict, topic: str, style: str = "professional") -> dict:
    api_key = get_env('ANTHROPIC_API_KEY')
    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    client = anthropic.Anthropic(api_key=api_key)

    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime("%B %d")
    week_end = today.strftime("%B %d, %Y")

    system_prompt = (
        "You are a senior financial markets analyst writing a weekly newsletter read by "
        "traders and serious investors. Your writing is sharp, opinionated, and data-driven. "
        "You give clear directional views — you don't hedge everything. "
        "You call out what matters and why. Return ONLY valid JSON with no markdown or code fences."
    )

    user_prompt = f"""Write the weekly markets newsletter for the week of {week_start}–{week_end}.

Topic: {topic}

Research data:
{json.dumps(research, indent=2)}

Return a JSON object with EXACTLY these keys:

- subject_line: punchy email subject line under 60 chars (include a key price or % move)
- headline: strong H1 title for the newsletter
- week_summary: 2-3 sentence executive summary of the week — what moved, why, what it means
- market_bias: list of objects, one per asset covered, each with:
    - asset: asset name (e.g. "Gold (XAU/USD)")
    - bias: "Bullish" or "Bearish"
    - direction: "Long" or "Short"
    - confidence: "High", "Medium", or "Low"
    - reasoning: 1-2 sentences explaining the bias with specific data points
    - support: key support level (price string)
    - resistance: key resistance level (price string)
- sections: list of 4-5 objects, each with:
    - title: section heading
    - body: 2-3 paragraphs of analysis. Be specific — cite actual prices, percentages, dates.
      Don't just describe what happened; explain what it means for next week.
- watch_next_week: list of 3-5 strings — specific events, data releases, or levels to monitor
- conclusion: 2-3 sentence closing with the single most important thing to watch
- citations_html: HTML <ul> list of sources with <a href> links

Be direct. If gold is in a clear uptrend, say "the path of least resistance is higher."
If EUR/USD looks like it's rolling over, say so and give the level that confirms it.
Return ONLY valid JSON."""

    print(f"[write_newsletter] Writing weekly newsletter for: {topic!r}")
    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=6000,
        messages=[{"role": "user", "content": user_prompt}],
        system=system_prompt,
    )

    raw_content = message.content[0].text

    try:
        result = json.loads(raw_content)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', raw_content)
        if match:
            result = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse JSON from Claude response: {raw_content[:200]}")

    out_path = os.path.join(tmp_dir, f"newsletter_{_slug(topic)}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"[write_newsletter] Done: {result.get('subject_line', '(no subject)')} → {out_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write weekly markets newsletter using Claude")
    parser.add_argument("--research", required=True, help="Path to research JSON file")
    parser.add_argument("--topic", required=True, help="Newsletter topic")
    parser.add_argument("--style", default="professional", choices=["professional", "casual", "technical"])
    args = parser.parse_args()

    with open(args.research) as f:
        research = json.load(f)

    result = write_newsletter(research, args.topic, args.style)
    print(json.dumps(result, indent=2))
