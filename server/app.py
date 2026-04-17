from flask import Flask, render_template, jsonify
from db import init_db, get_logs
from serial_arduino import monitor

app = Flask(__name__)

# Initialize DB when module loads
init_db()

@app.before_request
def start_serial():
    if not monitor.running:
        monitor.start()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/logs')
def api_logs():
    return jsonify(get_logs(20))

if __name__ == '__main__':
    monitor.start()
    app.run(host='0.0.0.0', port=5000, debug=False)
