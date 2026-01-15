# Benchling Canvas Flask App

Simple Flask app that creates a Benchling APP_HOMEPAGE canvas with text and buttons.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file from the example:
```bash
cp .env.example .env
```

3. Edit `.env` and add your credentials:
```
BENCHLING_API_KEY=your_actual_api_key
BENCHLING_TENANT=your-tenant-name
```

4. Run the app:
```bash
python app.py
```

The app will run on `http://localhost:5000`

## AWS AppRunner Deployment

### Step 1: Deploy to AppRunner
1. Create AppRunner service from source code
2. Go to **Configuration** → **Configure**
3. Under **Environment variables**, add:
   - `BENCHLING_API_KEY` = your_api_key
   - `BENCHLING_TENANT` = your_tenant
4. Deploy and note your AppRunner URL

### Step 2: Register App in Benchling
1. Update `manifest.yaml` with your AppRunner URL:
   ```yaml
   webhookUrl: https://your-apprunner-url.us-east-1.awsapprunner.com/webhook
   ```
2. In Benchling, go to **Settings** → **Developer Console**
3. Create a new app using the manifest
4. Install the app to your tenant
5. Navigate to the app's homepage to see your canvas

### Option 2: Using apprunner.yaml
The included `apprunner.yaml` configures the runtime. Set actual environment variables through the console (values in the file are placeholders).

**Note**: AppRunner will use gunicorn for production. The `.env` file is only for local development.

## Endpoints

- `POST /webhook` - Receives Benchling webhooks
- `GET /health` - Health check endpoint

## Usage

Point your Benchling app's webhook URL to `https://your-domain.com/webhook`

The app will automatically update the canvas when it receives an `v2.app.installed` webhook.