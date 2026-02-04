# Seqera Platform Integration for Benchling

A Benchling Canvas App that integrates with Seqera Platform, allowing users to search and view Nextflow pipeline runs directly within the Benchling interface.

## Overview

This application provides a seamless bridge between Benchling and Seqera Platform (formerly Nextflow Tower). Users can:
- Search for pipeline runs by name or keyword
- View detailed run information including status, timestamps, and labels
- Add run details to Benchling notebooks for documentation
- Track workflow execution status with visual indicators

The app uses Benchling's Canvas framework to provide an interactive UI within Benchling's web interface.

## Features

- **Pipeline Run Search**: Search across all accessible pipeline runs in your Seqera workspace
- **Status Visualization**: Clear status indicators using emojis (✅ Succeeded, ⚙️ Running, ❌ Failed, etc.)
- **Detailed Run Information**: View run names, projects, start times, duration, and custom labels
- **Notebook Integration**: Add run details directly to Benchling notebooks for record-keeping
- **Real-time Updates**: Canvas interface updates dynamically as users interact

## Prerequisites

- Python 3.11+
- Benchling tenant with Apps enabled
- Seqera Platform account with API access
- AWS Account with App Runner access (for deployment)
- GitHub repository (for App Runner deployment)

## Project Structure

```
.
├── local_app/
│   ├── benchling_app/
│   │   ├── views/
│   │   │   ├── canvas_initialize.py    # Landing page UI
│   │   │   ├── run_preview.py          # Pipeline run list view
│   │   │   ├── run_detail.py           # Detailed run information
│   │   │   └── constants.py            # UI element IDs
│   │   ├── canvas_interaction.py       # Button click handlers
│   │   ├── handler.py                  # Webhook routing
│   │   └── setup.py                    # App initialization
│   ├── lib/
│   │   ├── seqera_platform.py          # Seqera API integration
│   │   └── logger.py                   # Logging configuration
│   └── app.py                          # Flask application
├── tests/
│   ├── unit/                           # Unit tests
│   │   ├── local_app/
│   │   │   ├── benchling_app/
│   │   │   │   ├── test_canvas_interaction.py
│   │   │   │   └── views/
│   │   │   │       └── test_run_preview.py
│   │   │   ├── lib/
│   │   │   │   └── test_seqera_platform.py
│   │   │   └── test_app.py
│   ├── files/                          # Test fixtures
│   ├── helpers.py                      # Test utilities
│   └── conftest.py                     # Pytest configuration
├── requirements.txt                    # Python dependencies
├── Dockerfile                          # Container configuration
├── apprunner.yaml                      # AWS App Runner config
└── README.md
```

## Installation

### Local Development

1. **Clone the repository**
```bash
git clone https://github.com/robnewman/benchling-flask-demo.git
cd benchling-flask-demo
```

2. **Install dependencies**

Using uv (recommended):
```bash
uv sync
```

Or using pip:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set environment variables**

Create a `.env` file in the project root:
```bash
BENCHLING_APP_DEFINITION_ID=appdef_your_app_id
BENCHLING_CLIENT_ID=your_client_id
BENCHLING_CLIENT_SECRET=your_client_secret
```

4. **Run the application**
```bash
python3 -m gunicorn local_app.app:app --bind 0.0.0.0:8080
```

Or for development with auto-reload:
```bash
flask --app local_app.app run --debug --host 0.0.0.0 --port 8080
```

5. **Run tests**
```bash
pytest -v
```

## Dependencies

Key dependencies (see `requirements.txt` for full list):
- `flask==3.0.0` - Web framework
- `gunicorn==21.2.0` - WSGI HTTP server
- `benchling-sdk==1.23.0` - Benchling API client
- `requests==2.31.0` - HTTP library for Seqera API calls
- `python-dotenv==1.0.0` - Environment variable management
- `pytest==9.0.2` - Testing framework

## Benchling App Configuration

After creating your app in Benchling, configure the following settings in the App's configuration schema:

### Required Configuration Keys

| Key | Type | Description |
|-----|------|-------------|
| `seqeraApiEndpoint` | String | Seqera Platform API endpoint (e.g., `https://api.cloud.seqera.io` or `https://api.tower.nf`) |
| `seqeraPlatformToken` | String | Seqera Platform personal access token |
| `organizationName` | String | Your Seqera organization name |
| `workspaceName` | String | Your Seqera workspace name |
| `NXF_XPACK_LICENSE` | String | Nextflow XPack license key (if applicable) |

These values are configured per-tenant in the Benchling App's configuration interface and accessed via the `app.config_store` API.

## Docker

### Build locally
```bash
docker build -t seqera-benchling-app .
```

### Run locally
```bash
docker run -p 8080:8080 \
  -e BENCHLING_APP_DEFINITION_ID="your_app_def_id" \
  -e BENCHLING_CLIENT_ID="your_client_id" \
  -e BENCHLING_CLIENT_SECRET="your_client_secret" \
  seqera-benchling-app
```

## AWS App Runner Deployment

### Setup

1. **Push code to GitHub**
```bash
git add .
git commit -m "Deploy to App Runner"
git push origin main
```

2. **Create App Runner Service**
   - Go to AWS App Runner console
   - Click "Create service"
   - **Source**: Repository
   - **Repository provider**: GitHub
   - **Repository**: Select your repository
   - **Branch**: main
   - **Deployment trigger**: Automatic

3. **Configure Build**
   - **Configuration source**: Configuration file (apprunner.yaml)
   - The Dockerfile will handle the build and runtime configuration
   - **Port**: 8080

4. **Add Environment Variables**

In App Runner console under Configuration → Environment variables:

```
BENCHLING_APP_DEFINITION_ID=appdef_your_app_id
BENCHLING_CLIENT_ID=your_client_id
BENCHLING_CLIENT_SECRET=your_client_secret
```

⚠️ **Security Note**: Never commit sensitive credentials to version control. Always set them as environment variables in the App Runner console.

5. **Deploy**
   - Click "Create & deploy"
   - Wait for deployment to complete (5-10 minutes)
   - Note the service URL provided by App Runner

6. **Register Webhook in Benchling**
   - Go to your Benchling App settings
   - Set the webhook URL to: `https://your-app-runner-url.region.awsapprunner.com/1/webhooks/canvas`
   - Benchling will send Canvas webhooks to this endpoint

## Testing

The app includes a comprehensive test suite with 26 tests covering:
- Canvas interaction and routing (9 tests)
- UI rendering and block generation (9 tests)
- Seqera Platform API integration (8 tests)

### Run all tests
```bash
pytest -v
```

### Run specific test files
```bash
pytest tests/unit/local_app/lib/test_seqera_platform.py -v
```

### Run with coverage
```bash
pytest --cov=local_app --cov-report=html
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check endpoint for App Runner |
| POST | `/1/webhooks/<target>` | Benchling webhook receiver (handles canvas events) |

## Development Notes

### Why Python 3.11?
- `benchling-sdk>=1.21` requires Python 3.9+
- Python 3.11 provides better performance and type hints
- AWS App Runner supports Python 3.11 natively

### Why Custom Dockerfile?
App Runner's managed Python runtime uses multi-stage builds that don't always preserve pip installations correctly. A custom Dockerfile ensures all dependencies are available at runtime.

### Webhook Security
The app uses Benchling's webhook verification to ensure requests are authentic:
```python
verify(app_def_id, request.data.decode("utf-8"), request.headers)
```

Never skip this verification step in production.

### Threading vs. Queue
The current implementation uses threading for webhook processing:
```python
thread = Thread(target=handle_webhook, args=(request.json,))
```

**Production Recommendation**: For high-volume deployments, replace threading with a proper message queue (SQS, Redis, etc.) to handle webhook bursts and prevent thread exhaustion.

## Troubleshooting

### Common Issues

**ImportError: cannot import name 'Benchling'**
- Ensure you're using `from benchling_sdk.benchling import Benchling`
- Verify `benchling-sdk==1.23.0` is installed
- Check Python version is 3.11+

**"Could not retrieve user ID from user-info"**
- Verify your Seqera Platform token is valid and active
- Check that the API endpoint URL is correct (no trailing slash)
- Ensure your token has appropriate permissions in Seqera

**"Failed to fetch organization and workspace IDs"**
- Confirm organization and workspace names match exactly (case-sensitive)
- Verify your token has access to the specified workspace
- Check Seqera Platform API is accessible from your deployment

**Health check failures in App Runner**
- Verify app binds to `0.0.0.0:8080`
- Check application logs in App Runner console
- Ensure all environment variables are set
- Test the `/health` endpoint returns 200 OK

**Canvas not displaying**
- Verify webhook URL is registered in Benchling App settings
- Check webhook verification is passing (look for errors in logs)
- Ensure App Definition ID matches the environment variable

## Architecture

### Webhook Flow

1. User interacts with Canvas in Benchling
2. Benchling sends webhook to `/1/webhooks/<target>`
3. App verifies webhook signature
4. Handler routes to appropriate view function
5. View fetches data from Seqera Platform
6. Canvas is updated with new UI blocks
7. User sees updated interface

### Canvas States

1. **Landing Page**: Search input and "Get Workflows" button
2. **Results List**: Shows matching pipeline runs with status indicators
3. **Run Detail**: Detailed information about a specific run
4. **Notebook Entry**: Formatted run details added to Benchling notebook

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

(Add your license here)

## Support

For issues or questions:
- File an issue on GitHub
- Contact your Benchling representative
- Refer to [Benchling Apps documentation](https://docs.benchling.com/docs/apps-overview)
- Check [Seqera Platform API docs](https://docs.seqera.io/platform/latest/api/)
