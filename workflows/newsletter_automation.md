# Newsletter Automation Workflow

## Objective
Given a topic and optional style, research it, write a newsletter, generate an infographic, format it as HTML, and send it to FrankLe1997@hotmail.com (or any specified recipients).

## Prerequisites
- Xcode CLI tools installed (`xcode-select --install`)
- Virtual environment active: `source /Users/frank/Desktop/AI/.venv/bin/activate`
- `.env` populated with all keys (see below)

## Required .env Keys
```
ANTHROPIC_API_KEY
PERPLEXITY_API_KEY
NANOBANANA_API_KEY
GMAIL_SENDER         # your Gmail address
GMAIL_APP_PASSWORD   # 16-char App Password (Google Account → Security → App Passwords)
NEWSLETTER_RECIPIENT # default: FrankLe1997@hotmail.com
```

## Required Inputs
| Input | Example |
|-------|---------|
| `topic` | "The rise of AI agents in 2025" |
| `style` | `professional` \| `casual` \| `technical` (default: professional) |
| `recipients` | comma-separated emails, or leave blank to use default |

## Setup (one-time)
```bash
cd /Users/frank/Desktop/AI
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step-by-Step Execution

### Step 1: Research
```bash
python tools/research_topic.py --topic "YOUR TOPIC HERE"
```
- **Output:** `.tmp/research_{slug}.json`
- **Expect:** summary, 5-8 key_points, 5+ citations
- **On failure:**
  - `401`: Check `PERPLEXITY_API_KEY` in `.env`
  - Rate-limited: wait 60s, retry once
  - Invalid JSON output: re-run (model occasionally returns malformed JSON)

### Step 2: Write Newsletter
```bash
python tools/write_newsletter.py \
  --research .tmp/research_{slug}.json \
  --topic "YOUR TOPIC HERE" \
  --style professional
```
- **Output:** `.tmp/newsletter_{slug}.json`
- **Expect:** subject_line, headline, intro, 3-5 sections, conclusion, image_prompt, citations_html
- **On failure:**
  - `401`: Check `ANTHROPIC_API_KEY`
  - JSON parse error: re-run once — Claude occasionally wraps output in markdown

### Step 3: Generate Infographic
```bash
python tools/generate_infographic.py \
  --prompt "COPY image_prompt FROM newsletter JSON" \
  --hint "{slug}"
```
- **Output:** `.tmp/infographic_{slug}_{timestamp}.png`
- **Expect:** PNG image, typically 1024×1024px
- **On failure:**
  - Content policy rejection: simplify the prompt (remove specific faces, brands, logos)
  - Rate limit (15/day free tier): wait or skip this step (send text-only newsletter)
  - `API_KEY_INVALID`: Verify `NANOBANANA_API_KEY` is a valid Google AI Studio key

### Step 4: Format HTML
```bash
python tools/format_html.py \
  --newsletter .tmp/newsletter_{slug}.json \
  --images .tmp/infographic_{slug}_*.png
```
- **Output:** `.tmp/email_{slug}.html`
- **Preview:** Open in browser before sending to verify layout
- **On failure:** Re-run without `--images` to produce text-only version

### Step 5: Send Email
```bash
python tools/send_email.py \
  --html .tmp/email_{slug}.html \
  --subject "COPY subject_line FROM newsletter JSON"
```
- **Output:** Email delivered to `NEWSLETTER_RECIPIENT`
- **On failure:**
  - `Authentication failed` (535): Regenerate Gmail App Password
  - `SMTPRecipientsRefused`: Verify recipient email is correct
  - Connection timeout: Check network, retry after 30s

---

## Re-run Strategy
Each tool saves output to `.tmp/` before the next step. If a step fails:
- Check `.tmp/` for existing output — if it's good, skip to the next step
- Never re-run Steps 1-3 (API credits) unless the previous run definitively failed

## Cost Estimates (per newsletter)
| Step | API | Estimated cost |
|------|-----|---------------|
| Research | Perplexity sonar-pro | ~$0.003 |
| Write | Claude claude-sonnet-4-6 | ~$0.003 |
| Infographic | Gemini (free tier: 15/day) | $0.00 |
| Send | Gmail SMTP | $0.00 |
| **Total** | | **~$0.006** |

## Notes
- `.tmp/` files are disposable — safe to delete after sending
- Gemini image model (`gemini-2.0-flash-exp-image-generation`) is experimental; it may occasionally be unavailable
- Gmail App Password is separate from your Google account password — never commit it to git
