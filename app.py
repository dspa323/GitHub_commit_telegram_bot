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
JIRA_WEBHOOK_SECRET = os.getenv("JIRA_WEBHOOK_SECRET")
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").rstrip("/")
TELEGRAM_API_URL = (
    f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage" if BOT_TOKEN else None
)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "telegram_configured": bool(BOT_TOKEN and CHAT_ID),
        "jira_configured": bool(JIRA_BASE_URL or JIRA_WEBHOOK_SECRET),
    }


def send_telegram_message(message_text: str) -> None:
    if not BOT_TOKEN or not CHAT_ID or not TELEGRAM_API_URL:
        raise HTTPException(status_code=500, detail="Telegram configuration is missing")

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

    payload = await request.json()
    commits = payload.get("commits", [])
    if not commits:
        return Response(status_code=status.HTTP_200_OK)

    repository = payload.get("repository", {}).get("full_name", "Unknown repository")
    branch = payload.get("ref", "").removeprefix("refs/heads/")
    pusher = payload.get("pusher", {}).get("name", "Unknown")

    lines = [
        "🚀 <b>New GitHub push</b>",
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

    send_telegram_message("\n".join(lines))
    return Response(status_code=status.HTTP_200_OK)


@app.post("/jira/webhook")
async def jira_webhook(request: Request):
    if JIRA_WEBHOOK_SECRET:
        supplied_secret = request.query_params.get("secret", "")
        if not hmac.compare_digest(supplied_secret, JIRA_WEBHOOK_SECRET):
            raise HTTPException(status_code=401, detail="Invalid Jira webhook secret")

    payload = await request.json()
    event = payload.get("webhookEvent")

    if event != "jira:issue_created":
        return Response(status_code=status.HTTP_200_OK)

    issue = payload.get("issue", {})
    fields = issue.get("fields", {})
    key = str(issue.get("key", "Unknown issue"))
    summary = str(fields.get("summary", "No summary"))
    creator = fields.get("creator") or {}
    reporter = fields.get("reporter") or creator or {}
    issue_type = fields.get("issuetype") or {}
    priority = fields.get("priority") or {}
    project = fields.get("project") or {}

    issue_url = ""
    if JIRA_BASE_URL:
        issue_url = f"{JIRA_BASE_URL}/browse/{key}".replace(" ", "%20")

    title = (
        f'<a href="{html.escape(issue_url, quote=True)}">{html.escape(key)}</a>'
        if issue_url
        else html.escape(key)
    )
    lines = [
        "🎫 <b>New Jira task created</b>",
        title,
        f"Summary: {html.escape(summary)}",
        f"Type: {html.escape(str(issue_type.get('name', 'Unknown')))}",
        f"Project: {html.escape(str(project.get('name', project.get('key', 'Unknown'))))}",
        f"Priority: {html.escape(str(priority.get('name', 'Not set')))}",
        f"Reporter: {html.escape(str(reporter.get('displayName', 'Unknown')))}",
    ]

    send_telegram_message("\n".join(lines))
    return Response(status_code=status.HTTP_200_OK)