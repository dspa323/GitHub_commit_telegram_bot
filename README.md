# GitHub and Jira Notifications Bot

A FastAPI webhook service that sends Telegram group notifications for GitHub push events and newly created Jira issues.

## Render deployment

1. Create a new **Web Service** from this GitHub repository.
2. Use Python as the runtime.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add these environment variables in Render:
   - `TELEGRAM_BOT_TOKEN`: token from BotFather
   - `TELEGRAM_CHAT_ID`: numeric ID of the target Telegram chat
   - `GITHUB_WEBHOOK_SECRET`: optional GitHub webhook secret
   - `JIRA_WEBHOOK_SECRET`: optional secret appended to the Jira webhook URL
   - `JIRA_BASE_URL`: Jira site URL, for example `https://example.atlassian.net`

## GitHub webhook setup

1. Open the repository or organization **Settings > Webhooks > Add webhook**.
2. Payload URL: `https://<your-render-service>.onrender.com/webhook`
3. Content type: `application/json`
4. Secret: the same value used for `GITHUB_WEBHOOK_SECRET`, if enabled
5. Select **Just the push event**.

## Jira webhook setup

1. In Jira Cloud, open **Settings > System > WebHooks**.
2. Create a webhook for issue creation.
3. URL: `https://<your-render-service>.onrender.com/jira/webhook?secret=<JIRA_WEBHOOK_SECRET>`
4. If the secret is not configured in Render, omit the `?secret=...` part of the URL.
5. Choose **Created** as the issue event.

Only Jira's `jira:issue_created` webhook event is sent to Telegram. Jira Cloud webhook payloads contain issue key, summary, type, project, priority, and reporter information.

## Telegram setup

1. Create a bot with BotFather and copy its token.
2. Add the bot to the target Telegram group.
3. Send a message in the group and obtain the numeric chat ID from `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.

## Endpoints

- `GET /` — health check
- `POST /webhook` — GitHub push webhook
- `POST /jira/webhook` — Jira issue-created webhook

This service is intended for Render rather than Vercel.
