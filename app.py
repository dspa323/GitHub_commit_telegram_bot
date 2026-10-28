import os
import requests
import hashlib
import hmac
import html
from fastapi import FastAPI, HTTPException, Request, Response, status

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")
TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage" if BOT_TOKEN else None
)


@app.get("/")
def health_check():
    return {"status": "running", "telegram_configured": bool(BOT_TOKEN and CHAT_ID)}


@app.post("/webhook")
async def github_webhook(request: Request):
    if request.headers.get("X-GitHub-Event") != "push":
        return Response(status_code=status.HTTP_200_OK)

    body = await request.body()

    if WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(
            WEBHOOK_SECRET.encode(), body, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    if not BOT_TOKEN or not CHAT_ID:
        raise HTTPException(status_code=500, detail="Telegram configuration is missing")

    payload = await request.json()
    commits = payload.get("commits", [])
    if not commits:
        return Response(status_code=status.HTTP_200_OK)

    repository = payload.get("repository", {}).get("full_name", "Unknown repository")
    branch = payload.get("ref", "").removeprefix("refs/heads/")
    pusher = payload.get("pusher", {}).get("name", "Unknown")

    lines = [
        "🚀 <b>New push</b>",
        f"Repository: <code>{html.escape(str(repository))}</code>",
        f"Branch: <code>{html.escape(branch)}</code>",
        f"Author: {html.escape(str(pusher))}",
        "",
    ]

    for commit in commits:
        commit_id = str(commit.get("id", ""))[:7]
        message = str(commit.get("message", "No message")).split("\n", 1)[0]
        url = str(commit.get("url", ""))

        if url:
            lines.append(
                f'• <a href="{html.escape(url, quote=True)}">{html.escape(commit_id)}</a> '
                f"— {html.escape(message)}"
            )
        else:
            lines.append(f"• {html.escape(commit_id)} — {html.escape(message)}")

    message_text = "\n".join(lines)
    if len(message_text) > 4096:
        message_text = message_text[:4093] + "..."

    telegram_response = requests.post(
        TELEGRAM_API_URL,
        json={
            "chat_id": CHAT_ID,
            "text": message_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

    if telegram_response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Telegram API error: {telegram_response.text[:500]}",
        )

    return Response(status_code=status.HTTP_200_OK)