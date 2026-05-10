import json
import os
import subprocess
from datetime import datetime
from flask import Flask, jsonify, render_template

app = Flask(__name__)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSITIONS_FILE = os.path.join(BASE, "state", "positions.json")
LOGS_DIR = os.path.join(BASE, "logs")


def _systemctl(action, service):
    result = subprocess.run(
        ["sudo", "systemctl", action, service],
        capture_output=True, text=True
    )
    return result.returncode == 0


def _service_active(service):
    result = subprocess.run(
        ["systemctl", "is-active", service],
        capture_output=True, text=True
    )
    return result.stdout.strip() == "active"


def _read_positions():
    try:
        with open(POSITIONS_FILE) as f:
            return json.load(f)
    except Exception:
        return {"open_positions": [], "daily_losses": {}, "cooldown_until": None}


def _read_logs(n=60):
    lines = []
    today = datetime.now().strftime("%Y%m%d")
    for name in [f"signals_{today}.log", f"trades_{today}.log"]:
        path = os.path.join(LOGS_DIR, name)
        if os.path.exists(path):
            with open(path) as f:
                lines += f.readlines()
    lines.sort()
    return [l.rstrip() for l in lines[-n:]]


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def status():
    state = _read_positions()
    return jsonify({
        "bot_running": _service_active("trading-engine"),
        "gateway_running": _service_active("ibgateway"),
        "open_positions": state["open_positions"],
        "cooldown_until": state.get("cooldown_until"),
        "daily_losses": state.get("daily_losses", {}),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


@app.route("/api/logs")
def logs():
    return jsonify({"lines": _read_logs()})


@app.route("/api/start", methods=["POST"])
def start():
    ok = _systemctl("start", "trading-engine")
    return jsonify({"ok": ok})


@app.route("/api/stop", methods=["POST"])
def stop():
    ok = _systemctl("stop", "trading-engine")
    return jsonify({"ok": ok})


@app.route("/api/restart", methods=["POST"])
def restart():
    ok = _systemctl("restart", "trading-engine")
    return jsonify({"ok": ok})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
