import { schedules } from "@trigger.dev/sdk/v3";
import Anthropic from "@anthropic-ai/sdk";
import nodemailer from "nodemailer";

const PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions";

interface BriefingAnalysis {
  sentiment: "Bullish" | "Neutral" | "Bearish";
  confidence: "High" | "Medium" | "Low";
  tldr: string;
  shortTermBullets: string[];
  longTermBullets: string[];
}

async function fetchPerplexity(apiKey: string, query: string): Promise<string> {
  const res = await fetch(PERPLEXITY_URL, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: "sonar",
      messages: [{ role: "user", content: query }],
    }),
  });

  if (!res.ok) {
    throw new Error(`Perplexity error: ${res.status} ${res.statusText}`);
  }

  const data = (await res.json()) as { choices: { message: { content: string } }[] };
  return data.choices[0].message.content;
}

function buildEmailHtml(analysis: BriefingAnalysis, date: string): string {
  const sentimentColor =
    analysis.sentiment === "Bullish"
      ? "#16a34a"
      : analysis.sentiment === "Bearish"
      ? "#dc2626"
      : "#6b7280";

  const shortTermList = analysis.shortTermBullets
    .map((b) => `<li style="margin-bottom:6px">${b}</li>`)
    .join("");

  const longTermList = analysis.longTermBullets
    .map((b) => `<li style="margin-bottom:6px">${b}</li>`)
    .join("");

  return `<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family:system-ui,sans-serif;max-width:600px;margin:0 auto;padding:24px;background:#f9fafb">
  <div style="background:#fff;border-radius:12px;padding:28px;box-shadow:0 1px 3px rgba(0,0,0,.1)">

    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px">
      <div>
        <h1 style="margin:0;font-size:22px;font-weight:700;color:#111">₿ BTC Daily Briefing</h1>
        <p style="margin:4px 0 0;color:#6b7280;font-size:14px">${date}</p>
      </div>
      <span style="background:${sentimentColor};color:#fff;font-weight:700;font-size:13px;padding:6px 14px;border-radius:20px;letter-spacing:.5px">
        ${analysis.sentiment.toUpperCase()} · ${analysis.confidence}
      </span>
    </div>

    <div style="background:#f0fdf4;border-left:4px solid ${sentimentColor};padding:12px 16px;border-radius:4px;margin-bottom:24px">
      <p style="margin:0;font-size:15px;color:#111;font-style:italic">${analysis.tldr}</p>
    </div>

    <h2 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#6b7280;margin:0 0 10px">
      📰 Short-Term (24h)
    </h2>
    <ul style="margin:0 0 24px;padding-left:20px;color:#374151;font-size:14px;line-height:1.6">
      ${shortTermList}
    </ul>

    <h2 style="font-size:14px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;color:#6b7280;margin:0 0 10px">
      🔭 Long-Term Outlook
    </h2>
    <ul style="margin:0 0 24px;padding-left:20px;color:#374151;font-size:14px;line-height:1.6">
      ${longTermList}
    </ul>

    <hr style="border:none;border-top:1px solid #e5e7eb;margin:20px 0">
    <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center">
      Powered by Perplexity + Claude · Delivered daily at 09:00 Amsterdam time
    </p>
  </div>
</body>
</html>`;
}

export const btcDailyBriefing = schedules.task({
  id: "btc-daily-briefing",
  cron: {
    pattern: "0 9 * * *",
    timezone: "Europe/Amsterdam",
  },
  retry: {
    maxAttempts: 3,
    factor: 2,
    minTimeoutInMs: 5_000,
    maxTimeoutInMs: 30_000,
  },
  run: async () => {
    const perplexityKey = process.env.PERPLEXITY_API_KEY;
    const anthropicKey = process.env.ANTHROPIC_API_KEY;
    const gmailSender = process.env.GMAIL_SENDER;
    const gmailPassword = process.env.GMAIL_APP_PASSWORD;
    const recipient = process.env.RECIPIENT_EMAIL;

    if (!perplexityKey) throw new Error("PERPLEXITY_API_KEY is not set");
    if (!anthropicKey) throw new Error("ANTHROPIC_API_KEY is not set");
    if (!gmailSender) throw new Error("GMAIL_SENDER is not set");
    if (!gmailPassword) throw new Error("GMAIL_APP_PASSWORD is not set");
    if (!recipient) throw new Error("RECIPIENT_EMAIL is not set");

    console.log("Fetching BTC news from Perplexity...");

    const [shortTermRaw, longTermRaw] = [
      await fetchPerplexity(
        perplexityKey,
        "What happened with Bitcoin (BTC) in the last 24 hours? Include price movements, key market events, whale activity, exchange flows, and overall market sentiment."
      ),
      await fetchPerplexity(
        perplexityKey,
        "What is the long-term Bitcoin (BTC) outlook for 2025? Cover institutional adoption, ETF flows, macro factors (inflation, rate cuts), on-chain metrics like MVRV and NVT, and notable analyst price targets."
      ),
    ];

    console.log("Analyzing with Claude...");

    const anthropic = new Anthropic({ apiKey: anthropicKey });

    const message = await anthropic.messages.create({
      model: "claude-sonnet-4-6",
      max_tokens: 1024,
      messages: [
        {
          role: "user",
          content: `You are a concise crypto analyst. Analyze the Bitcoin data below and respond with ONLY valid JSON — no markdown, no explanation, nothing else.

SHORT-TERM NEWS (last 24h):
${shortTermRaw}

LONG-TERM OUTLOOK (2025):
${longTermRaw}

Required JSON format:
{
  "sentiment": "Bullish" | "Neutral" | "Bearish",
  "confidence": "High" | "Medium" | "Low",
  "tldr": "One crisp sentence summarising the overall BTC situation right now.",
  "shortTermBullets": ["3 to 5 short bullet points about last 24h"],
  "longTermBullets": ["3 to 5 short bullet points about the long-term outlook"]
}`,
        },
      ],
    });

    const rawText =
      message.content[0].type === "text" ? message.content[0].text.trim() : "{}";

    const analysis: BriefingAnalysis = JSON.parse(rawText);

    const date = new Date().toLocaleDateString("en-GB", {
      weekday: "short",
      day: "numeric",
      month: "short",
      year: "numeric",
    });

    const html = buildEmailHtml(analysis, date);

    console.log(`Sending email to ${recipient}...`);

    const transporter = nodemailer.createTransport({
      host: "smtp.gmail.com",
      port: 465,
      secure: true,
      auth: { user: gmailSender, pass: gmailPassword },
    });

    await transporter.sendMail({
      from: `"BTC Briefing" <${gmailSender}>`,
      to: recipient,
      subject: `[BTC] ${date} — ${analysis.sentiment} (${analysis.confidence} confidence)`,
      html,
    });

    console.log("Briefing sent successfully.");
    return { sentiment: analysis.sentiment, confidence: analysis.confidence, recipient };
  },
});
