import os
import json
import secrets
import time
import sys
from flask import Flask, request, redirect, render_template, make_response, send_from_directory, abort

app = Flask(__name__, template_folder=".", static_folder=None)
startTime = time.time()
ANALYTICS = {}

@app.before_request
def count_requests():
    path = request.path
    ANALYTICS[path] = ANALYTICS.get(path, 0) + 1

# Load the secret passkey from the environment variable.
REGISTRATION_PASSKEY = os.getenv("REGISTRATION_PASSKEY", "mysecretpasskey")

LINKS_FILE = "./links.json"

# Load LINKS from file if exists, otherwise initialize empty dictionary.
if os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "r") as f:
        LINKS = json.load(f)
else:
    LINKS = {}

SESSIONS = set()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/hot-takes")
def hot_takes():
    return render_template("hot-takes.html")

@app.route("/hot-takes.html")
def hot_takes_redirect():
    return redirect("/hot-takes")

@app.route("/index.html")
def index():
    return redirect("/")

# Serve static files manually.
@app.route("/homestyles.css")
def homestyles():
    return send_from_directory(".", "homestyles.css")

@app.route("/homescripts.js")
def homescripts():
    return send_from_directory(".", "homescripts.js")

@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "favicon.ico")

@app.route("/robots.txt")
def robots():
    return send_from_directory(".", "robots.txt")

@app.route("/sitemap.xml")
def sitemap():
    return send_from_directory(".", "sitemap.xml")

@app.route("/bs.mp4")
def bs_mp4():
    return send_from_directory(".", "bs.mp4")

@app.route("/heartbeat")
def heartbeat():
    return "I'm alive!"

@app.route("/info")
def info():
    uptime = time.time() - startTime
    return (
        f"Built with love and caffeine using Flask.\nFlask version: {Flask.__version__}\n"
        f"Python version: {sys.version}\nUptime: {uptime}\n"
    )

# --- Authentication and UI Routes ---

@app.route("/login", methods=["GET"])
def login_form():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def login():
    passkey = request.form.get("passkey", "")
    if passkey == REGISTRATION_PASSKEY:
        token = secrets.token_hex(16)
        SESSIONS.add(token)
        response = make_response(redirect("/add-link-form"))
        response.set_cookie("session", token, httponly=True, secure=True)
        return response
    return "Unauthorized", 401

@app.route("/add-link-form")
def add_link_form():
    token = request.cookies.get("session")
    if token not in SESSIONS:
        return redirect("/login")
    return render_template("add_link.html")

@app.route("/add-link", methods=["POST"])
def add_link():
    token = request.cookies.get("session")
    if token not in SESSIONS:
        return "Unauthorized", 401
    alias = request.form.get("alias")
    target_url = request.form.get("url")
    if not alias or not target_url:
        return "Missing alias or url field", 400
    LINKS[alias] = target_url
    with open(LINKS_FILE, "w") as f:
        json.dump(LINKS, f)
    return f"Alias /{alias} registered to {target_url}"

# Route to redirect short links.
@app.route("/<alias>")
def redirect_alias(alias):
    if alias in LINKS:
        return redirect(LINKS[alias])
    return "Not found", 404

@app.route("/insights")
def usage_insights():
    data = {
        "uptime": time.time() - startTime,
        "registered_links": len(LINKS),
        "active_sessions": len(SESSIONS),
        "request_counts": ANALYTICS,
    }
    return render_template("insights.html", data=data)

if __name__ == "__main__":
    app.run()