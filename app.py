from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Configuration - loaded from .env file
BENCHLING_CLIENT_ID = os.environ.get('BENCHLING_CLIENT_ID')
BENCHLING_CLIENT_SECRET = os.environ.get('BENCHLING_CLIENT_SECRET')
BENCHLING_TENANT = os.environ.get('BENCHLING_TENANT', 'your-tenant')

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle incoming webhooks from Benchling"""
    data = request.json
    
    print(f"Received webhook: {data.get('type')}")
    
    # Handle app installation
    if data.get('type') == 'v2.app.installed':
        canvas_id = data.get('canvasId')
        if canvas_id:
            update_canvas(canvas_id)
    
    return jsonify({"status": "ok"}), 200

@app.route('/webhook/lifecycle', methods=['POST'])
def lifecycle_webhook_handler():
    """Handle app lifecycle webhooks from Benchling"""
    data = request.json
    
    message_type = data.get('message', {}).get('type')
    print(f"Received lifecycle webhook: {message_type}")
    
    # Handle app installation
    if message_type == 'v2.app.installed':
        # App was installed - you can perform initialization here
        print(f"App installed in tenant: {data.get('tenantId')}")
    
    return jsonify({"status": "ok"}), 200

def update_canvas(canvas_id):
    """Update the canvas with text and buttons"""
    canvas_update = {
        "blocks": [
            {
                "id": "welcome_text",
                "type": "MARKDOWN",
                "text": "### Welcome to My App\nThis is a simple homepage with text and buttons."
            },
            {
                "id": "action_button",
                "type": "BUTTON",
                "text": "Click Me",
                "enabled": True
            }
        ],
        "enabled": True
    }
    
    url = f"https://{BENCHLING_TENANT}.benchling.com/api/v2/app-canvases/{canvas_id}"
    headers = {
        "Content-Type": "application/json"
    }
    
    # Use Basic Auth with CLIENT_ID and CLIENT_SECRET
    response = requests.patch(
        url, 
        json=canvas_update, 
        headers=headers,
        auth=(BENCHLING_CLIENT_ID, BENCHLING_CLIENT_SECRET)
    )
    
    if response.status_code == 200:
        print(f"Canvas updated successfully: {canvas_id}")
    else:
        print(f"Failed to update canvas: {response.status_code} - {response.text}")
    
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)