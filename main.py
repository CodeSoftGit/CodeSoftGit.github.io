import os
import json
import secrets
import time
import sys
import re
import logging
import redis
from urllib.parse import urlparse
from flask import (
    Flask,
    request,
    redirect,
    render_template,
    make_response,
    send_from_directory,
    abort,
    url_for,
)
from flask_wtf.csrf import CSRFProtect
from markupsafe import escape

app = Flask(__name__, template_folder=".", static_folder=None)
# Set a secret key for session and CSRF protection.
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", secrets.token_hex(16))
csrf = CSRFProtect(app)
startTime = time.time()

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://...")
try:
    redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
except Exception as e:
    logging.error(f"Redis connection error: {e}")
    sys.exit("Failed to connect to Redis.")

# Load the secret passkey from the environment variable.
REGISTRATION_PASSKEY = os.getenv("REGISTRATION_PASSKEY", "pass...")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", None)

@app.before_request
def count_requests():
    path = request.path
    try:
        redis_client.hincrby("analytics", path, 1)
    except Exception as e:
        logging.error(f"Error updating analytics for path {path}: {e}")

@app.errorhandler(404)
def page_not_found(e):
    return redirect("https://http.cat/images/404.jpg")

@app.errorhandler(500)
def server_error(e):
    return redirect("https://http.cat/images/500.jpg")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/hot-takes")
def hot_takes():
    return render_template("hot-takes.html")

@app.route("/hot-takes.html")
def hot_takes_redirect():
    return redirect(url_for("hot_takes"))

@app.route("/index.html")
def index():
    return redirect(url_for("home"))

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
        try:
            redis_client.sadd("sessions", token)
        except Exception as e:
            logging.error(f"Error creating session: {e}")
            abort(500)
        response = make_response(redirect(url_for("add_link_form")))
        # Set cookie with expiration and SameSite flag.
        response.set_cookie("session", token, httponly=True, secure=True, samesite="Strict", max_age=3600)
        return response
    return "Unauthorized", 401

@app.route("/add-link-form")
def add_link_form():
    token = request.cookies.get("session")
    if not token or not redis_client.sismember("sessions", token):
        return redirect(url_for("login_form"))
    return render_template("add_link.html")

@app.route("/add-link", methods=["POST"])
def add_link():
    token = request.cookies.get("session")
    if not token or not redis_client.sismember("sessions", token):
        return "Unauthorized", 401
    alias = request.form.get("alias")
    target_url = request.form.get("url")
    if not alias or not target_url:
        return "Missing alias or url field", 400

    # Validate alias: allow only alphanumerics, dashes, and underscores.
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", alias):
        return "Invalid alias", 400

    # Validate target_url: only allow HTTP and HTTPS protocols.
    parsed_url = urlparse(target_url)
    if parsed_url.scheme not in ["http", "https"]:
        return "Invalid URL scheme", 400

    try:
        redis_client.hset("links", alias, target_url)
    except Exception as e:
        logging.error(f"Error storing link: {e}")
        abort(500)
    return f"Alias /{escape(alias)} registered to {escape(target_url)}"

# Route to redirect short links.
@app.route("/<alias>")
def redirect_alias(alias):
    try:
        target_url = redis_client.hget("links", alias)
    except Exception as e:
        logging.error(f"Error fetching alias {alias}: {e}")
        abort(500)
    if target_url:
        parsed_url = urlparse(target_url)
        if parsed_url.scheme not in ["http", "https"]:
            logging.error(f"Invalid URL scheme for alias {alias}: {target_url}")
            abort(400)
        return redirect(target_url)
    return "Not found", 404

@app.route("/insights")
def usage_insights():
    try:
        data = {
            "uptime": time.time() - startTime,
            "registered_links": redis_client.hlen("links"),
            "active_sessions": redis_client.scard("sessions"),
            "request_counts": redis_client.hgetall("analytics"),
        }
    except Exception as e:
        logging.error(f"Error fetching insights: {e}")
        abort(500)
    return render_template("insights.html", data=data)

def get_gemini_response(query, **kwargs):
    import base64
    import os
    from google import genai
    from google.genai import types
    
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.0-flash-lite"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(
                    text=query,
                ),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.9,
        top_k=40,
        max_output_tokens=2048,
        safety_settings=[
          types.SafetySetting(
              category="HARM_CATEGORY_HARASSMENT",
              threshold="BLOCK_MEDIUM_AND_ABOVE", # Block some
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_HATE_SPEECH",
              threshold="BLOCK_MEDIUM_AND_ABOVE", # Block some
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
              threshold="BLOCK_LOW_AND_ABOVE", # Block most
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_DANGEROUS_CONTENT",
              threshold="BLOCK_MEDIUM_AND_ABOVE", # Block some
          ),
          types.SafetySetting(
              category="HARM_CATEGORY_CIVIC_INTEGRITY",
              threshold="BLOCK_LOW_AND_ABOVE", # Block most
          ),
      ],
        response_mime_type="text/plain",
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
    )
    return response.text

@app.route("/ai/<model>", methods=["POST"])
def ai(model):
    # Rate limit: 5 requests per minute per IP
    ip = request.remote_addr
    rate_limit_key = f"rate_limit:{ip}"
    try:
        count = redis_client.incr(rate_limit_key)
        if count == 1:
            redis_client.expire(rate_limit_key, 60)
        if count > 5:
            return "Rate limit exceeded. Try again later.", 429
    except Exception as e:
        logging.error(f"Error handling rate limit for IP {ip}: {e}")

    if model == "gemini":
        if not GEMINI_API_KEY:
            return "Service unavailable. Please try again later or contact your sysadmin.", 503
        try:
            query = request.form.get("query", "")
            if not query.strip():
                return "Please provide a valid query.", 400
            response = get_gemini_response(query)
        except Exception as e:
            logging.error(f"Error fetching Gemini response: {e}")
            abort(500)
        return response
    else:
        return "Invalid model", 400
    
@app.route("/ai")
def chat_ui():
    return render_template("chat.html")