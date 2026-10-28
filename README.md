# GitHub to Telegram Push Bot

A FastAPI webhook service that sends Telegram group notifications when GitHub push events contain commits.

## Render deployment

1. Create a new **Web Service** from this GitHub repository.
2. Use Python as the runtime.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`
5. Add these environment variables in Render:
   - `TELEGRAM_BOT_TOKEN`: token from BotFather
   - `TELEGRAM_CHAT_ID`: numeric ID (or username) of the target Telegram chat
   - `GITHUB_WEBHOOK_SECRET`: a random secret used to verify GitHub webhook signatures

## Telegram setup

1. Create a bot with BotFather and copy its token.
2. Add the bot to the target Telegram group.
3. Send a message in the group, then obtain the chat ID from `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`.
4. Invite the bot to the group with permission to post messages.

## GitHub webhook setup

For the GitHub repository or organization:

1. Open **Settings > Webhooks > Add webhook**.
2. Payload URL: `https://<your-render-service>.onrender.com/webhook`
3. Content type: `application/json`
4. Secret: the same value used for `GITHUB_WEBHOOK_SECRET`
5. Select **Just the push event**.

## Endpoint

- `GET /` — health check
- `POST /webhook` — GitHub push webhook

This service is intended for Render. Vercel is not needed. The bot does not require a Vercel build command, environment configuration, or start command when deployed on Render.
