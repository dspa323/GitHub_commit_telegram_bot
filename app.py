import os
import requests
from fastapi import FastAPI, Request, Response, status

app = FastAPI()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

@app.get("/")
def health_check():
    return {"status": "running"}

@app.post("/webhook")
async def github_webhook(request: Request):
    event = request.headers.get("X-GitHub-Event")
    
    # We only care about push events
    if event != "push":
        return Response(status_code=status.HTTP_200_OK)

    payload = await request.json()
    commits = payload.get("commits", [])
    if not commits:
        return Response(status_code=status.HTTP_200_OK)

    repo_name = payload.get("repository", {}).get("full_name", "Unknown Repo")
    branch = payload.get("ref", "").replace("refs/heads/", "")
    pusher = payload.get("pusher", {}).get("name", "Unknown")

    # Build markdown message
    lines = [
        f"🚀 *New Push to* `{repo_name}` (`{branch}`)",
        f"👤 *Author:* {pusher}\n"
    ]

    for c in commits:
        commit_id = c.get("id", "")[:7]
        msg = c.get("message", "").split("\n")[0]
        url = c.get("url", "")
        lines.append(f"• [{commit_id}]({url}) - {msg}")

    message_text = "\n".join(lines)

    # Forward to Telegram
    requests.post(
        TELEGRAM_API_URL,
        json={
            "chat_id": CHAT_ID,
            "text": message_text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True
        },
        timeout=10
    )

    return Response(status_code=status.HTTP_200_OK)