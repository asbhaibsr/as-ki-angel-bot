"""
Keep-alive server to prevent bot from sleeping on hosting platforms
"""
from flask import Flask
from threading import Thread
import time
import requests
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "As ki Angel Bot is alive and running! 🤖"

@app.route('/health')
def health():
    return {"status": "healthy", "bot": "running"}

def run():
    try:
        app.run(host='0.0.0.0', port=8080)
    except OSError:
        # If port 8080 is busy, try 8081
        app.run(host='0.0.0.0', port=8081)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

def ping_self():
    """Ping the keep-alive server every 5 minutes to prevent sleeping"""
    while True:
        try:
            time.sleep(300)  # Wait 5 minutes
            requests.get("http://localhost:8080/health", timeout=10)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
