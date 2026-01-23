# Benchling Flask Demo

A Flask application integrated with Benchling SDK, deployed on AWS App Runner.

## Prerequisites

- Python 3.11+
- AWS Account with App Runner access
- Benchling account and API credentials
- GitHub repository (for App Runner deployment)

## Project Structure
```
.
├── local_app/
│   ├── __init__.py
│   └── app.py          # Main Flask application
├── requirements.txt     # Python dependencies
├── Dockerfile          # Container configuration
└── README.md
```

## Installation

### Local Development

1. **Clone the repository**
```bash
   git clone https://github.com/robnewman/benchling-flask-demo.git
   cd benchling-flask-demo
```

2. **Create a virtual environment**
```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
   pip install -r requirements.txt
```

4. **Set environment variables**
```bash
   export BENCHLING_API_KEY="your_api_key_here"
   export BENCHLING_TENANT="your_tenant_url"
   # Add other required environment variables
```

5. **Run the application**
```bash
   python3 -m gunicorn local_app.app:app --bind 0.0.0.0:8080
```

   Or for development:
```bash
   cd local_app
   flask run
```

## Dependencies

Key dependencies (see `requirements.txt` for full list):
- `flask==3.0.0` - Web framework
- `gunicorn==21.2.0` - WSGI HTTP server
- `benchling-sdk==1.23.0` - Benchling API client
- `requests==2.31.0` - HTTP library
- `python-dotenv==1.0.0` - Environment variable management

## Docker

### Build locally
```bash
docker build -t benchling-flask-demo .
```

### Run locally
```bash
docker run -p 8080:8080 \
  -e BENCHLING_API_KEY="your_api_key" \
  -e BENCHLING_TENANT="your_tenant" \
  benchling-flask-demo
```

## AWS App Runner Deployment

### Setup

1. **Push code to GitHub**
```bash
   git add .
   git commit -m "Initial commit"
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
   - **Configuration source**: Configuration file
   - Or manually:
     - **Runtime**: Python 3.11
     - **Build command**: (leave empty - Dockerfile handles it)
     - **Start command**: (leave empty - Dockerfile handles it)
     - **Port**: 8080

4. **Add Environment Variables**

## Environment Variables

The following environment variables must be configured in App Runner:

- `BENCHLING_CLIENT_ID` - Your Benchling OAuth client ID
- `BENCHLING_CLIENT_SECRET` - Your Benchling OAuth client secret  
- `BENCHLING_TENANT` - Your Benchling tenant URL (e.g., `https://your-tenant.benchling.com`)

⚠️ **Important**: Override the placeholder values in `apprunner.yaml` by setting real values in the App Runner console under Configuration → Environment variables.

5. **Deploy**
   - Click "Create & deploy"
   - Wait for deployment to complete (~5-10 minutes)

### Troubleshooting

**ImportError: cannot import name 'Benchling'**
- Ensure you're using `from benchling_sdk.benchling import Benchling`
- Verify `benchling-sdk==1.23.0` is in requirements.txt
- Check Python version is 3.11+ (older versions don't support 1.23.0)

**Module not found errors**
- Ensure `local_app/__init__.py` exists (can be empty)
- Verify Dockerfile copies all files correctly
- Check that start command references correct module path: `local_app.app:app`

**Health check failures**
- Verify app binds to `0.0.0.0:8080`
- Check application logs in App Runner console
- Ensure environment variables are set correctly

## Development Notes

### Why Python 3.11?
- `benchling-sdk>=1.21` requires Python 3.9+
- Python 3.8 only supports up to `benchling-sdk==1.20`

### Why Custom Dockerfile?
App Runner's managed Python 3.11 runtime uses multi-stage builds that don't preserve pip installations in the runtime container. A custom Dockerfile ensures all dependencies are available at runtime.

### Folder Structure
The app is in `local_app/` to demonstrate Python package imports. For a simpler structure, you could move `app.py` to the root and update the gunicorn command to `app:app`.

## API Endpoints

```
GET  /              # Home page
POST /webhook       # Benchling webhook handler
POST /webhook/canvas # 
...
```

## License

(Add your license here)

## Contributing

(Add contribution guidelines here)