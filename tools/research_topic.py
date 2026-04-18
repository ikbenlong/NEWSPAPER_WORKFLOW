import argparse
import json
import os
import re

import requests
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)


def get_env(key):
    val = os.getenv(key)
    if not val or not val.strip():
        raise ValueError(f"Missing env var: {key}")
    return val.strip()


def _slug(text):
    return re.sub(r'[^a-z0-9]+', '_', text.lower())[:40].strip('_')


def research_topic(topic: str) -> dict:
    api_key = get_env('PERPLEXITY_API_KEY')
    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)

    system_prompt = (
        "You are a financial markets research analyst. Given a topic, return a JSON object "
        "with EXACTLY these keys:\n"
        "- summary: 2-3 paragraph overview of this week's market action\n"
        "- weekly_performance: list of objects, one per asset, each with keys: "
        "  'asset' (name), 'weekly_change' (e.g. '+2.3%'), 'current_price' (e.g. '$4,450'), "
        "  'weekly_high', 'weekly_low', 'key_move' (one sentence on the main driver)\n"
        "- key_events: list of 5-8 strings describing the most important news/events this week\n"
        "- upcoming_events: list of 3-5 strings for next week's key risk events "
        "  (e.g. Fed meeting, CPI, ECB)\n"
        "- citations: list of objects with 'title' and 'url' keys\n"
        "Return ONLY valid JSON. No markdown, no code fences."
    )

    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": (
                f"Research this week's market performance and news for: {topic}. "
                "Focus on price action, key drivers, and notable events from the past 7 days."
            )},
        ],
        "max_tokens": 3000,
        "temperature": 0.2,
        "search_recency_filter": "week",
        "return_citations": True,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    print(f"[research_topic] Querying Perplexity (last 7 days) for: {topic!r}")
    response = requests.post(
        "https://api.perplexity.ai/chat/completions",
        json=payload,
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]
    api_citations = data.get("citations", [])

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        match = re.search(r'\{[\s\S]*\}', raw_content)
        if match:
            parsed = json.loads(match.group())
        else:
            parsed = {"summary": raw_content, "weekly_performance": [], "key_events": [], "upcoming_events": [], "citations": []}

    if not parsed.get("citations") and api_citations:
        parsed["citations"] = [
            {"title": c.get("title", c), "url": c.get("url", c)}
            if isinstance(c, dict) else {"title": c, "url": c}
            for c in api_citations
        ]

    result = {
        "topic": topic,
        "summary": parsed.get("summary", ""),
        "weekly_performance": parsed.get("weekly_performance", []),
        "key_events": parsed.get("key_events", []),
        "upcoming_events": parsed.get("upcoming_events", []),
        "citations": parsed.get("citations", []),
        "raw_response": raw_content,
    }

    out_path = os.path.join(tmp_dir, f"research_{_slug(topic)}.json")
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)

    assets = len(result['weekly_performance'])
    print(f"[research_topic] Done: {assets} assets tracked, "
          f"{len(result['key_events'])} events, {len(result['citations'])} citations → {out_path}")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Research weekly market data using Perplexity")
    parser.add_argument("--topic", required=True, help="Market topic to research")
    args = parser.parse_args()
    result = research_topic(args.topic)
    print(json.dumps(result, indent=2))
