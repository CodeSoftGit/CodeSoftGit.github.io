import os
import json
import secrets
import time
import sys

from sanic import Sanic
from sanic.response import text, redirect
from mangum import Mangum
from jinja2 import FileSystemLoader
from sanic_jinja2 import SanicJinja2

app = Sanic("Portfolio")
jinja = SanicJinja2(app, loader=FileSystemLoader("."))
startTime = time.time()

ANALYTICS = {}

@app.middleware('request')
async def count_requests(request):
    path = request.path
    ANALYTICS[path] = ANALYTICS.get(path, 0) + 1

# Load the secret passkey from the environment variable.
# Set REGISTRATION_PASSKEY in your environment (e.g., using set REGISTRATION_PASSKEY=your_secure_key on Windows)
REGISTRATION_PASSKEY = os.getenv("REGISTRATION_PASSKEY", "mysecretpasskey")

LINKS_FILE = "./links.json"

# Load LINKS from file if exists, otherwise initialize empty dictionary.
if os.path.exists(LINKS_FILE):
    with open(LINKS_FILE, "r") as f:
        LINKS = json.load(f)
else:
    LINKS = {}

SESSIONS = set()

@app.get("/")
async def home(request):
    return jinja.render("index.html", request)

@app.get("/hot-takes")
async def hot_takes(request):
    return jinja.render("hot-takes.html", request)

@app.get("/hot-takes.html")
async def hot_takes_redirect(request):
    return redirect("/hot-takes")

@app.get("/index.html")
async def index(_):
    return redirect("/")

# Serve static files using built-in static middleware with explicit unique route names
app.static('/homestyles.css', './homestyles.css', name="static-homestyles")
app.static('/homescripts.js', './homescripts.js', name="static-homescripts")

@app.get("/heartbeat")
async def heartbeat(_):
    return text("I'm alive!")

@app.get("/info")
async def info(_):
    uptime = time.time() - startTime
    return text(
        f"Built with love and caffeine using Sanic.\nSanic version: {Sanic.__version__}\n"
        f"Python version: {sys.version}\nUptime: {uptime}\n"
    )

# --- Authentication and UI Routes ---

@app.get("/login")
async def login_form(request):
    return jinja.render("login.html", request)

@app.post("/login")
async def login(request):
    form_data = await request.form()
    passkey = form_data.get("passkey", "")
    if passkey == REGISTRATION_PASSKEY:
        # Generate a secure token for this session.
        token = secrets.token_hex(16)
        SESSIONS.add(token)
        response = redirect("/add-link-form")
        # Set cookie with HttpOnly and secure flags (secure flag is effective over HTTPS)
        response.cookies["session"] = token
        response.cookies["session"]["httponly"] = True
        response.cookies["session"]["secure"] = True
        return response
    return text("Unauthorized", status=401)

@app.get("/add-link-form")
async def add_link_form(request):
    token = request.cookies.get("session")
    if token not in SESSIONS:
        return redirect("/login")
    return jinja.render("add_link.html", request)

# Protected endpoint that expects form submission and saves updated LINKS to a file.
@app.post("/add-link")
async def add_link(request):
    token = request.cookies.get("session")
    if token not in SESSIONS:
        return text("Unauthorized", status=401)
    form_data = await request.form()
    alias = form_data.get("alias")
    target_url = form_data.get("url")
    if not alias or not target_url:
        return text("Missing alias or url field", status=400)
    LINKS[alias] = target_url
    # Save the updated LINKS dictionary to file.
    with open(LINKS_FILE, "w") as f:
        json.dump(LINKS, f)
    return text(f"Alias /{alias} registered to {target_url}")

# Route to redirect short links
@app.get("/<alias>")
async def redirect_alias(request, alias):
    if alias in LINKS:
        return redirect(LINKS[alias])
    return text("Not found", status=404)

@app.get("/insights")
async def usage_insights(request):
    data = {
        "uptime": time.time() - startTime,
        "registered_links": len(LINKS),
        "active_sessions": len(SESSIONS),
        "request_counts": ANALYTICS,
    }
    return jinja.render("insights.html", request, data=data)

handler = Mangum(app._asgi_app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)