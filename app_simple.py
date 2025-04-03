from flask import Flask, render_template
import os

app = Flask(__name__)

@app.route('/')
def index():
    return "Hello from Guards & Robbers! The app is running."

@app.route('/health')
def health():
    return {"status": "ok", "message": "Application is healthy"}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000))) 