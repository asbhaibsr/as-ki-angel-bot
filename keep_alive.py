import os
import time
import requests
from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "As ki Angel Bot is alive and running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

def run_flask_app():
    """Runs the Flask app."""
    port = int(os.environ.get("PORT", 8080))
    try:
        app.run(host='0.0.0.0', port=port)
    except OSError as e:
        print(f"Error running Flask app: {e}")
        # Fallback to another port if 8080 is busy (less common on Koyeb)
        # This part might not be needed for Koyeb, but good to have.
        app.run(host='0.0.0.0', port=8081)

def keep_alive():
    """Starts the Flask app in a separate thread."""
    t = Thread(target=run_flask_app)
    t.daemon = True
    t.start()

def ping_self():
    """Ping the keep-alive server every 5 minutes to prevent sleeping"""
    while True:
        try:
            time.sleep(300)  # Wait 5 minutes
            requests.get(f"http://127.0.0.1:{os.environ.get('PORT', 8080)}/health", timeout=10)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
