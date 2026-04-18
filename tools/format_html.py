import argparse
import json
import os
import re
from datetime import datetime

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'), override=True)

# Brand colours from le_financial_newspaper_brand.svg
GOLD        = "#C9A84C"
GOLD_LIGHT  = "#E8D5A3"
GOLD_DIM    = "#7a6030"
BLACK       = "#0a0a0a"
BLACK_SOFT  = "#111111"
GRAY_TEXT   = "#888888"

BIAS_COLORS = {
    "Bullish": {"bg": "#0f2d1a", "text": "#4caf76", "border": "#2d6e47"},
    "Bearish": {"bg": "#2d0f0f", "text": "#e05c5c", "border": "#8b2020"},
}
DIRECTION_COLORS = {
    "Long":  {"bg": "#2d6e47", "text": "#ffffff"},
    "Short": {"bg": "#8b2020", "text": "#ffffff"},
}
CONFIDENCE_COLORS = {
    "High":   {"bg": "#2a2200", "text": "#C9A84C"},
    "Medium": {"bg": "#1e1e1e", "text": "#aaaaaa"},
    "Low":    {"bg": "#161616", "text": "#666666"},
}

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="X-UA-Compatible" content="IE=edge">
  <meta name="x-apple-disable-message-reformatting">
  <title>{subject_line}</title>
</head>
<body style="margin:0;padding:0;background-color:#1a1a1a;font-family:Georgia,serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#1a1a1a;padding:24px 0;">
  <tr><td align="center">
  <table width="620" cellpadding="0" cellspacing="0" style="background-color:#0a0a0a;border-radius:4px;overflow:hidden;border:1px solid #2a2200;">

    <!-- Logo header (inline SVG) -->
    <tr>
      <td style="background-color:#0a0a0a;padding:0;text-align:center;line-height:0;">
        {logo_svg}
      </td>
    </tr>

    <!-- Gold rule -->
    <tr><td style="padding:0 40px;"><hr style="border:none;border-top:1px solid {gold_dim};margin:0;"></td></tr>

    <!-- Headline + date -->
    <tr>
      <td style="background-color:#0f0f0f;padding:28px 40px 24px;text-align:center;">
        <h1 style="margin:0 0 10px;color:{gold_light};font-family:Georgia,serif;font-size:22px;font-weight:700;line-height:1.4;">{headline}</h1>
        <p style="margin:0;color:{gray};font-family:Arial,sans-serif;font-size:12px;letter-spacing:2px;text-transform:uppercase;">{date_range}</p>
      </td>
    </tr>

    <!-- Gold rule -->
    <tr><td><hr style="border:none;border-top:1px solid {gold_dim};margin:0;"></td></tr>

    <!-- Week Summary -->
    <tr>
      <td style="padding:24px 40px 20px;border-bottom:1px solid #1e1e1e;">
        <p style="margin:0;color:#cccccc;font-family:Georgia,serif;font-size:14px;line-height:1.9;font-style:italic;">{week_summary}</p>
      </td>
    </tr>

    <!-- Market Bias Table -->
    <tr>
      <td style="padding:24px 40px 16px;">
        <p style="margin:0 0 14px;font-family:Arial,sans-serif;font-size:10px;font-weight:700;color:{gold};letter-spacing:3px;text-transform:uppercase;">Market Bias Summary</p>
        {bias_table}
      </td>
    </tr>

    <!-- Gold rule -->
    <tr><td style="padding:0 40px;"><hr style="border:none;border-top:1px solid #1e1e1e;margin:0;"></td></tr>

    <!-- Analysis Sections -->
    {sections_html}

    <!-- Watch Next Week -->
    <tr>
      <td style="padding:20px 40px 28px;background-color:#0d0d0d;border-top:1px solid #1e1e1e;border-bottom:1px solid #1e1e1e;">
        <p style="margin:0 0 12px;font-family:Arial,sans-serif;font-size:10px;font-weight:700;color:{gold};letter-spacing:3px;text-transform:uppercase;">Watch Next Week</p>
        {watch_html}
      </td>
    </tr>

    <!-- Conclusion -->
    <tr>
      <td style="padding:24px 40px 28px;">
        <p style="margin:0;color:#cccccc;font-family:Georgia,serif;font-size:14px;line-height:1.9;border-left:3px solid {gold};padding-left:16px;">{conclusion}</p>
      </td>
    </tr>

    <!-- Gold rule -->
    <tr><td style="padding:0 40px;"><hr style="border:none;border-top:1px solid #1e1e1e;margin:0;"></td></tr>

    <!-- Sources -->
    <tr>
      <td style="padding:20px 40px;">
        <p style="margin:0 0 8px;font-family:Arial,sans-serif;color:#555;font-size:10px;letter-spacing:2px;text-transform:uppercase;">Sources</p>
        <div style="color:#666;font-family:Arial,sans-serif;font-size:12px;line-height:2.0;">{citations_html}</div>
      </td>
    </tr>

    <!-- Footer -->
    <tr>
      <td style="background-color:#000000;padding:16px 40px;text-align:center;border-top:1px solid #2a2200;">
        <p style="margin:0;color:#444;font-family:Arial,sans-serif;font-size:11px;line-height:1.7;">
          Le Financial NewsPaper &nbsp;·&nbsp; For informational purposes only, not financial advice.<br>
          To unsubscribe, reply with "unsubscribe" in the subject line.
        </p>
      </td>
    </tr>

  </table>
  </td></tr>
</table>
</body>
</html>
"""

SECTION_TEMPLATE = """\
<tr>
  <td style="padding:24px 40px 12px;">
    <h2 style="margin:0 0 10px;color:{gold_light};font-family:Georgia,serif;font-size:17px;font-weight:700;border-bottom:1px solid #2a2200;padding-bottom:8px;">{title}</h2>
    <p style="margin:0;color:#bbbbbb;font-family:Georgia,serif;font-size:14px;line-height:2.0;">{body}</p>
  </td>
</tr>"""


def _load_logo_inline() -> str:
    logo_path = os.path.join(os.path.dirname(__file__), '..', 'Logo', 'le_financial_newspaper_brand.svg')
    if not os.path.exists(logo_path):
        return ""
    with open(logo_path, "r", encoding="utf-8") as f:
        svg = f.read()
    # Ensure the SVG fills the container width for email
    svg = re.sub(r'width="[^"]*"', 'width="100%"', svg, count=1)
    return svg


def _bias_row(item: dict) -> str:
    asset      = item.get("asset", "")
    bias       = item.get("bias", "Bullish")
    direction  = item.get("direction", "Long")
    confidence = item.get("confidence", "Medium")
    reasoning  = item.get("reasoning", "")
    support    = item.get("support", "—")
    resistance = item.get("resistance", "—")

    bc = BIAS_COLORS.get(bias, BIAS_COLORS["Bullish"])
    dc = DIRECTION_COLORS.get(direction, DIRECTION_COLORS["Long"])
    cc = CONFIDENCE_COLORS.get(confidence, CONFIDENCE_COLORS["Medium"])

    bias_badge = (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:2px;'
        f'background-color:{bc["bg"]};color:{bc["text"]};border:1px solid {bc["border"]};'
        f'font-family:Arial,sans-serif;font-size:11px;font-weight:700;">{bias}</span>'
    )
    dir_badge = (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:2px;'
        f'background-color:{dc["bg"]};color:{dc["text"]};'
        f'font-family:Arial,sans-serif;font-size:11px;font-weight:700;">{direction}</span>'
    )
    conf_badge = (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:2px;'
        f'background-color:{cc["bg"]};color:{cc["text"]};'
        f'font-family:Arial,sans-serif;font-size:10px;">{confidence} conviction</span>'
    )

    return f"""\
<tr style="border-bottom:1px solid #1a1a1a;">
  <td style="padding:12px 0;vertical-align:top;width:150px;">
    <p style="margin:0;font-family:Georgia,serif;font-size:13px;font-weight:700;color:{GOLD_LIGHT};">{asset}</p>
    <p style="margin:4px 0 0;font-family:Arial,sans-serif;font-size:10px;color:#555;">S: {support} &nbsp;·&nbsp; R: {resistance}</p>
  </td>
  <td style="padding:12px 8px;vertical-align:top;width:80px;">{bias_badge}</td>
  <td style="padding:12px 8px;vertical-align:top;width:60px;">{dir_badge}</td>
  <td style="padding:12px 0 12px 8px;vertical-align:top;">
    {conf_badge}
    <p style="margin:6px 0 0;font-family:Arial,sans-serif;font-size:12px;color:#888;line-height:1.6;">{reasoning}</p>
  </td>
</tr>"""


def format_html(newsletter: dict) -> str:
    today = datetime.now()
    date_range = today.strftime("Week of %B %d, %Y")

    logo_svg = _load_logo_inline()

    biases = newsletter.get("market_bias", [])
    if biases:
        rows = "\n".join(_bias_row(b) for b in biases)
        bias_table = (
            f'<table width="100%" cellpadding="0" cellspacing="0" '
            f'style="border-collapse:collapse;border-top:1px solid #1a1a1a;">'
            f'{rows}</table>'
        )
    else:
        bias_table = ""

    sections_html = "\n".join(
        SECTION_TEMPLATE.format(
            gold_light=GOLD_LIGHT,
            title=s.get("title", ""),
            body=s.get("body", "").replace("\n", "<br><br>"),
        )
        for s in newsletter.get("sections", [])
    )

    watch_items = newsletter.get("watch_next_week", [])
    if watch_items:
        items_html = "".join(
            f'<li style="margin-bottom:8px;font-family:Arial,sans-serif;font-size:13px;color:#aaaaaa;">{item}</li>'
            for item in watch_items
        )
        watch_html = f'<ul style="margin:0;padding-left:18px;line-height:1.8;">{items_html}</ul>'
    else:
        watch_html = ""

    citations_html = newsletter.get("citations_html", "")
    citations_html = citations_html.replace("<a ", f'<a style="color:{GOLD_DIM};" ')

    html = TEMPLATE.format(
        subject_line=newsletter.get("subject_line", "Weekly Markets Report"),
        logo_svg=logo_svg,
        headline=newsletter.get("headline", ""),
        date_range=date_range,
        week_summary=newsletter.get("week_summary", ""),
        bias_table=bias_table,
        sections_html=sections_html,
        watch_html=watch_html,
        conclusion=newsletter.get("conclusion", ""),
        citations_html=citations_html,
        gold=GOLD,
        gold_light=GOLD_LIGHT,
        gold_dim=GOLD_DIM,
        gray=GRAY_TEXT,
    )

    slug = re.sub(r'[^a-z0-9]+', '_', newsletter.get("subject_line", "newsletter").lower())[:40]
    tmp_dir = os.path.join(os.path.dirname(__file__), '..', '.tmp')
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, f"email_{slug}.html")
    with open(out_path, "w") as f:
        f.write(html)

    print(f"[format_html] HTML formatted ({len(html):,} chars) → {out_path}")
    return html


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Format weekly newsletter as HTML email")
    parser.add_argument("--newsletter", required=True, help="Path to newsletter JSON file")
    args = parser.parse_args()

    with open(args.newsletter) as f:
        newsletter = json.load(f)

    html = format_html(newsletter)
    print(f"HTML length: {len(html):,} chars")
