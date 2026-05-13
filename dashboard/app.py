import json
import os
import subprocess
from datetime import datetime
from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "kt-dash-9f3a2b1c"

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSITIONS_FILE = os.path.join(BASE, "state", "positions.json")
LOGS_DIR = os.path.join(BASE, "logs")

USERNAME = "Tfab2021"
PASSWORD = "Davejr1011!"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated


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


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form.get("username") == USERNAME and request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        error = "Invalid credentials"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/status")
@api_login_required
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
@api_login_required
def logs():
    return jsonify({"lines": _read_logs()})


@app.route("/api/start", methods=["POST"])
@api_login_required
def start():
    ok = _systemctl("start", "trading-engine")
    return jsonify({"ok": ok})


@app.route("/api/stop", methods=["POST"])
@api_login_required
def stop():
    ok = _systemctl("stop", "trading-engine")
    return jsonify({"ok": ok})


@app.route("/api/restart", methods=["POST"])
@api_login_required
def restart():
    ok = _systemctl("restart", "trading-engine")
    return jsonify({"ok": ok})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
