"""
Going Merry — Web Application
==============================
Multi-user viral shorts factory platform.
Flask-based web app with JWT auth, social account linking, and automated clip pipeline.
"""

import os
import sys
from pathlib import Path
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# ── Path Setup ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
ROOT_DIR = BASE_DIR.parent

# Ensure project root is importable
sys.path.insert(0, str(ROOT_DIR))

# ── Flask App Init ───────────────────────────────────────────────────────────
app = Flask(__name__, 
            template_folder=str(BASE_DIR / "templates"),
            static_folder=str(BASE_DIR / "static"))

app.config.update(
    SECRET_KEY=os.getenv("FLASK_SECRET_KEY", "going-merry-secret-change-in-prod-2026"),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'going_merry.db'}"),
    SQLALCHEMY_ENGINE_OPTIONS={"connect_args": {"timeout": 30}},
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    MAX_CONTENT_LENGTH=500 * 1024 * 1024,  # 500MB upload limit
)

# ── Extensions ───────────────────────────────────────────────────────────────
db      = SQLAlchemy(app)
bcrypt  = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "auth.login"
login_manager.login_message = "Please log in to access Going Merry."
login_manager.login_message_category = "info"

# ── User Loader ─────────────────────────────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    from web_app.models import User
    return User.query.get(int(user_id))

# Register blueprints
from web_app.routes.auth        import auth_bp        # noqa: E402
from web_app.routes.dashboard   import dash_bp        # noqa: E402
from web_app.routes.clips       import clips_bp       # noqa: E402
from web_app.routes.social      import social_bp      # noqa: E402
from web_app.routes.influencers import influencers_bp # noqa: E402
from web_app.routes.platform_auth import platform_auth_bp # noqa: E402
from web_app.routes.pipeline    import pipeline_bp    # noqa: E402

app.register_blueprint(auth_bp)
app.register_blueprint(dash_bp)
app.register_blueprint(clips_bp)
app.register_blueprint(social_bp)
app.register_blueprint(influencers_bp)
app.register_blueprint(platform_auth_bp)
app.register_blueprint(pipeline_bp)

# ── Real-Time SSE Event Streaming ──────────────────────────────────────────
import json
import time
import queue
from flask import Response, stream_with_context, jsonify, request
from clipper.core.event_bus import bus

@app.route("/api/events")
def stream_events():
    """Server-Sent Events endpoint streaming real-time pipeline events."""
    def event_stream():
        q = bus.register_queue()
        try:
            yield f"data: {json.dumps({'type': 'connected', 'timestamp': time.time()})}\n\n"
            while True:
                try:
                    event = q.get(timeout=20.0)
                    yield f"data: {json.dumps(event.to_dict())}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            bus.unregister_queue(q)

    response = Response(stream_with_context(event_stream()), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response

@app.route("/api/events/history")
def event_history():
    """Retrieve buffered events since a given event ID."""
    since_id = request.args.get("since_id", 0, type=int)
    return jsonify({"events": bus.get_events(since_id=since_id)})

# ── Create Tables ────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
