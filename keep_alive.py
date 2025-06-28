import os
import time
import requests
from threading import Thread # <-- यह लाइन जोड़ें
from flask import Flask # <-- सुनिश्चित करें कि यह मौजूद है

app = Flask(__name__)

@app.route('/')
def home():
    return "As ki Angel Bot is alive and running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

def run_flask_app(): # <-- फ़ंक्शन का नाम बदला
    """Runs the Flask app."""
    # Koyeb assigns a port via the PORT environment variable
    port = int(os.environ.get("PORT", 8080)) # PORT env var का उपयोग करें, या 8080 डिफ़ॉल्ट
    try:
        app.run(host='0.0.0.0', port=port)
    except OSError as e:
        print(f"Error running Flask app: {e}")
        # Fallback to another port if 8080 is busy (less common on Koyeb)
        app.run(host='0.0.0.0', port=8081)

def keep_alive():
    """Starts the Flask app in a separate thread."""
    t = Thread(target=run_flask_app) # <-- यहाँ run_flask_app को टारगेट करें
    t.daemon = True # <-- daemon thread बनाएं ताकि मेन प्रोग्राम बंद होने पर यह भी बंद हो जाए
    t.start()

def ping_self():
    """Ping the keep-alive server every 5 minutes to prevent sleeping"""
    # Use localhost as Flask app runs on 0.0.0.0 and is accessible locally
    # Or, if deployed, ping the actual Koyeb public URL if it's available.
    # For now, local ping is usually enough for Koyeb to detect activity.
    while True:
        try:
            time.sleep(300)  # Wait 5 minutes
            requests.get(f"http://127.0.0.1:{os.environ.get('PORT', 8080)}/health", timeout=10)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
