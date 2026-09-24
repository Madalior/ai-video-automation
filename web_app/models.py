"""
Going Merry — Database Models
"""
from datetime import datetime
from flask_login import UserMixin
from web_app.app import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    niche         = db.Column(db.String(50), default="gaming")
    niche_prompt  = db.Column(db.Text, default="")
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    social_accounts       = db.relationship("SocialAccount", backref="user", lazy=True, cascade="all, delete-orphan")
    account_personas      = db.relationship("AccountPersona", backref="user", lazy=True, cascade="all, delete-orphan")
    system_settings       = db.relationship("SystemSetting", backref="user", lazy=True, cascade="all, delete-orphan")
    clips                 = db.relationship("Clip", backref="user", lazy=True, cascade="all, delete-orphan")
    upload_jobs           = db.relationship("UploadJob", backref="user", lazy=True, cascade="all, delete-orphan")
    monitored_influencers = db.relationship("MonitoredInfluencer", backref="user", lazy=True, cascade="all, delete-orphan")
    campaign_briefs       = db.relationship("CampaignBrief", backref="user", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.username}>"


class AccountPersona(db.Model):
    """
    Groups and isolates multiple social media channels (YouTube, Instagram, Facebook, TikTok)
    under a specific account username / channel identity.
    Matches user requirement: 'separate the accounts that this username account have these yt, ig, fb and other platform'.
    """
    __tablename__ = "account_personas"

    id               = db.Column(db.String(50), primary_key=True)   # e.g. "acc_01", "acc_02"
    user_id          = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    username         = db.Column(db.String(80), nullable=False)     # e.g. "@SpeedViralClips"
    name             = db.Column(db.String(120), default="")        # e.g. "Speed Clips Network"
    gmail            = db.Column(db.String(120), default="")        # Linked operator Gmail address
    content_type     = db.Column(db.String(50), default="whop_content") # whop_content | upload_based
    niche            = db.Column(db.String(50), default="general")
    fleet            = db.Column(db.String(50), default="whop")
    proxy            = db.Column(db.String(250), default="")
    # Platform handles & statuses
    youtube_handle   = db.Column(db.String(120), default="")
    youtube_status   = db.Column(db.String(30), default="not_connected")    # not_connected | connected
    instagram_handle = db.Column(db.String(120), default="")
    instagram_status = db.Column(db.String(30), default="not_connected")
    facebook_handle  = db.Column(db.String(120), default="")
    facebook_status  = db.Column(db.String(30), default="not_connected")
    tiktok_handle    = db.Column(db.String(120), default="")
    tiktok_status    = db.Column(db.String(30), default="not_connected")
    
    is_active        = db.Column(db.Boolean, default=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    clips            = db.relationship("Clip", backref="account_persona", lazy=True)

    def __repr__(self):
        return f"<AccountPersona {self.id} ({self.username})>"

    def to_dict(self):
        # Fetch verified disk reality (zero fantasy)
        disk_status = {}
        try:
            from clipper.uploader.platform_auth_manager import PlatformAuthManager
            disk_status = PlatformAuthManager().get_account_platform_status(self.id)
        except Exception:
            pass

        yt_info = disk_status.get("youtube", {})
        ig_info = disk_status.get("instagram", {})
        fb_info = disk_status.get("facebook", {})
        tt_info = disk_status.get("tiktok", {})

        return {
            "id": self.id,
            "username": self.username,
            "name": self.name or self.username,
            "gmail": self.gmail,
            "content_type": self.content_type,
            "niche": self.niche,
            "fleet": self.fleet,
            "proxy": self.proxy,
            "platforms": {
                "youtube": {
                    "handle": yt_info.get("handle") or self.youtube_handle or f"{self.username}_yt",
                    "status": "connected" if yt_info.get("connected") else (self.youtube_status if self.youtube_status == "connected" else "not_connected"),
                    "connected": yt_info.get("connected", False),
                    "channel_title": yt_info.get("channel_title", ""),
                    "subscribers": yt_info.get("subscribers", 0)
                },
                "instagram": {
                    "handle": ig_info.get("handle") or self.instagram_handle or f"{self.username}_ig",
                    "status": "connected" if ig_info.get("connected") else (self.instagram_status if self.instagram_status == "connected" else "not_connected"),
                    "connected": ig_info.get("connected", False),
                },
                "facebook": {
                    "handle": fb_info.get("handle") or self.facebook_handle or f"{self.username}_fb",
                    "status": "connected" if fb_info.get("connected") else (self.facebook_status if self.facebook_status == "connected" else "not_connected"),
                    "connected": fb_info.get("connected", False),
                },
                "tiktok": {
                    "handle": tt_info.get("handle") or self.tiktok_handle or f"{self.username}_tt",
                    "status": "connected" if tt_info.get("connected") else (self.tiktok_status if self.tiktok_status == "connected" else "not_connected"),
                    "connected": tt_info.get("connected", False),
                },
            },
            "is_active": self.is_active,
            "clips_count": len(self.clips) if self.clips else 0
        }


class SystemSetting(db.Model):
    """
    Key-value store for user/system configuration (e.g. viral view criteria, Telegram credentials).
    """
    __tablename__ = "system_settings"

    id         = db.Column(db.Integer, primary_key=True)
    user_id    = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    key        = db.Column(db.String(100), nullable=False)
    value      = db.Column(db.Text, default="")
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SystemSetting {self.key}={self.value[:20]}>"


class SocialAccount(db.Model):
    __tablename__ = "social_accounts"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    platform       = db.Column(db.String(20), nullable=False)  # instagram, tiktok, youtube, facebook
    channel_name   = db.Column(db.String(120), default="")
    channel_id     = db.Column(db.String(120), default="")
    follower_count = db.Column(db.Integer, default=0)
    cookies_json   = db.Column(db.Text, default="")             # encrypted browser cookies
    is_active      = db.Column(db.Boolean, default=True)
    added_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SocialAccount {self.platform} ({self.channel_name}) for user {self.user_id}>"


class MonitoredInfluencer(db.Model):
    """
    Influencers / Creators that Going Merry follows and monitors daily for completed livestreams.
    """
    __tablename__ = "monitored_influencers"

    id              = db.Column(db.Integer, primary_key=True)
    user_id         = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    channel_name    = db.Column(db.String(120), nullable=False)   # e.g. "IShowSpeed"
    channel_handle  = db.Column(db.String(120), default="")       # e.g. "@IShowSpeed"
    channel_url     = db.Column(db.Text, nullable=False)          # streams tab or channel url
    platform        = db.Column(db.String(30), default="youtube") # youtube | twitch | kick
    is_active       = db.Column(db.Boolean, default=True)
    num_clips       = db.Column(db.Integer, default=5)            # Clips to generate per stream
    target_platform = db.Column(db.String(30), default="all")     # all | tiktok | shorts | reels
    auto_upload     = db.Column(db.Boolean, default=True)
    last_checked_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_stream_id  = db.Column(db.String(100), default="")
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    streams = db.relationship("ProcessedStream", backref="influencer", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MonitoredInfluencer {self.channel_name} ({self.platform})>"


class ProcessedStream(db.Model):
    """
    Individual completed livestreams fetched by StreamMonitor to prevent duplicate processing.
    """
    __tablename__ = "processed_streams"

    id            = db.Column(db.Integer, primary_key=True)
    influencer_id = db.Column(db.Integer, db.ForeignKey("monitored_influencers.id"), nullable=False)
    stream_id     = db.Column(db.String(100), nullable=False)     # YouTube video ID or Twitch VOD ID
    stream_title  = db.Column(db.String(250), default="")
    stream_url    = db.Column(db.Text, nullable=False)
    duration      = db.Column(db.Float, default=0.0)
    status        = db.Column(db.String(30), default="queued")    # queued | processing | completed | failed
    clip_count    = db.Column(db.Integer, default=0)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at  = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<ProcessedStream {self.stream_id} - {self.status}>"


class Clip(db.Model):
    __tablename__ = "clips"

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    source_url     = db.Column(db.Text, nullable=False)
    clip_path      = db.Column(db.Text, default="")
    title          = db.Column(db.String(200), default="")
    hook           = db.Column(db.Text, default="")
    score          = db.Column(db.Integer, default=0)
    start_time     = db.Column(db.Float, default=0.0)
    end_time       = db.Column(db.Float, default=0.0)
    duration       = db.Column(db.Float, default=0.0)
    hashtags       = db.Column(db.Text, default="")   # JSON list
    status         = db.Column(db.String(20), default="processing")  # processing | ready | uploading | posted | failed
    post_url       = db.Column(db.Text, default="")   # Live URL on YouTube/TikTok/Reels
    views          = db.Column(db.Integer, default=0)
    likes          = db.Column(db.Integer, default=0)
    comments       = db.Column(db.Integer, default=0)
    shares         = db.Column(db.Integer, default=0)
    scheduled_time = db.Column(db.String(30), default="")
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    last_tracked_at= db.Column(db.DateTime, nullable=True)

    # Multi-account persona & Viral tracking
    account_persona_id   = db.Column(db.String(50), db.ForeignKey("account_personas.id"), nullable=True)
    is_viral             = db.Column(db.Boolean, default=False)
    viral_criteria_views = db.Column(db.Integer, default=1000)
    viral_alert_sent     = db.Column(db.Boolean, default=False)
    viral_notified_at    = db.Column(db.DateTime, nullable=True)

    # Relationships
    upload_jobs = db.relationship("UploadJob", backref="clip", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Clip {self.title[:30]} score={self.score}>"


class UploadJob(db.Model):
    __tablename__ = "upload_jobs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    clip_id     = db.Column(db.Integer, db.ForeignKey("clips.id"), nullable=False)
    platform    = db.Column(db.String(20), nullable=False)  # instagram, tiktok, youtube, facebook
    caption     = db.Column(db.Text, default="")
    status      = db.Column(db.String(20), default="pending")  # pending | uploading | done | failed
    error_msg   = db.Column(db.Text, default="")
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<UploadJob {self.platform} status={self.status}>"


class CampaignBrief(db.Model):
    """
    Structured extraction of a Whop Content Rewards campaign.
    Contains every requirement the AI browser agent read from the campaign page.
    """
    __tablename__ = "campaign_briefs"

    id                    = db.Column(db.Integer, primary_key=True)
    user_id               = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    campaign_name         = db.Column(db.String(250), nullable=False)
    campaign_url          = db.Column(db.Text, nullable=False)
    cpm_rate              = db.Column(db.Float, default=1.0)         # $ per 1000 views
    budget_remaining      = db.Column(db.Float, default=0.0)         # $ left in bounty pool
    # Source material
    source_video_links    = db.Column(db.Text, default="[]")         # JSON list of URLs
    # Content requirements
    required_hashtags     = db.Column(db.Text, default="[]")         # JSON list e.g. ["#brand", "#ad"]
    required_sound_name   = db.Column(db.String(250), default="")    # Name of required TikTok sound
    required_sound_url    = db.Column(db.Text, default="")           # URL to download the sound
    sound_volume_level    = db.Column(db.String(50), default="")     # e.g. "70%", "background", "full"
    min_duration_sec      = db.Column(db.Integer, default=15)
    max_duration_sec      = db.Column(db.Integer, default=90)
    # Audience demographics
    tier1_enabled         = db.Column(db.Boolean, default=False)
    tier1_min_pct         = db.Column(db.Integer, default=40)        # 40% Tier-1 country views
    tier1_countries       = db.Column(db.Text, default='["US","UK","CA","AU","NZ","DE","FR"]')
    # Verification
    verification_required = db.Column(db.Boolean, default=False)     # TikTok Video Pre-Check
    analytics_screenshot  = db.Column(db.Boolean, default=False)     # Needs demographic screenshot
    # Posting rules
    posting_platforms     = db.Column(db.Text, default='["tiktok","youtube_shorts","instagram_reels"]')
    forbidden_content     = db.Column(db.Text, default="[]")         # JSON list of banned topics
    keep_public_days      = db.Column(db.Integer, default=90)        # Keep post visible X days
    additional_notes      = db.Column(db.Text, default="")           # Free-text extra rules
    # Status tracking
    status                = db.Column(db.String(30), default="active")  # active | paused | depleted | completed
    clips_submitted       = db.Column(db.Integer, default=0)
    total_views_earned    = db.Column(db.Integer, default=0)
    total_earnings        = db.Column(db.Float, default=0.0)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)
    last_scanned_at       = db.Column(db.DateTime, nullable=True)

    # Relationships
    submissions = db.relationship("CampaignSubmission", backref="campaign", lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CampaignBrief {self.campaign_name} CPM=${self.cpm_rate}>"


class CampaignSubmission(db.Model):
    """
    Tracks each individual clip submitted to a Whop campaign.
    Records the live post URL, submission status, and view count.
    """
    __tablename__ = "campaign_submissions"

    id              = db.Column(db.Integer, primary_key=True)
    campaign_id     = db.Column(db.Integer, db.ForeignKey("campaign_briefs.id"), nullable=False)
    clip_id         = db.Column(db.Integer, db.ForeignKey("clips.id"), nullable=True)
    platform        = db.Column(db.String(30), nullable=False)        # tiktok | youtube_shorts | instagram_reels
    live_post_url   = db.Column(db.Text, default="")                  # The actual TikTok/YT/IG link
    whop_status     = db.Column(db.String(30), default="pending")     # pending | submitted | approved | rejected
    rejection_reason= db.Column(db.Text, default="")
    views_at_submit = db.Column(db.Integer, default=0)
    earnings        = db.Column(db.Float, default=0.0)
    screenshot_path = db.Column(db.Text, default="")                  # Path to analytics screenshot
    submitted_at    = db.Column(db.DateTime, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<CampaignSubmission {self.platform} {self.whop_status}>"


class TaskQueueItem(db.Model):
    """
    Persistent message queue table corresponding to the REDIS layer in architecture_flowchart.md.
    Provides bulletproof FIFO job queuing whether Redis is running or using local SQLite fallback.
    """
    __tablename__ = "task_queue_items"

    id           = db.Column(db.Integer, primary_key=True)
    job_id       = db.Column(db.String(64), unique=True, nullable=False)
    job_type     = db.Column(db.String(32), nullable=False)  # clip_job | stream_job | whop_job
    payload_json = db.Column(db.Text, nullable=False, default="{}")
    status       = db.Column(db.String(24), default="queued") # queued | processing | completed | failed
    priority     = db.Column(db.Integer, default=0)
    result_json  = db.Column(db.Text, default="{}")
    error_msg    = db.Column(db.Text, default="")
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    started_at   = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<TaskQueueItem {self.job_id} ({self.job_type}) [{self.status}]>"


def seed_master_user(username: str = "admin", password: str = "Booma@07", email: str = "captain@goingmerry.ai") -> User:
    """
    Ensures master account exists matching flowchart credentials (default password: Booma@07).
    """
    from web_app.app import bcrypt
    user = User.query.filter_by(username=username).first()
    if not user:
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        user = User(username=username, email=email, password_hash=pw_hash)
        db.session.add(user)
        db.session.commit()
        print(f"[AUTH] Master user '{username}' seeded successfully.")
    return user


def migrate_db():
    """
    Safely ensures all required tables and columns exist in SQLite without data loss.
    """
    from web_app.app import app, db
    import json
    import os

    with app.app_context():
        db.create_all()
        try:
            conn = db.engine.raw_connection()
            cur = conn.cursor()
            
            # Check clips columns
            cur.execute("PRAGMA table_info(clips)")
            existing_clip_cols = {row[1] for row in cur.fetchall()}
            clip_cols = [
                ("post_url", "TEXT DEFAULT ''"),
                ("views", "INTEGER DEFAULT 0"),
                ("likes", "INTEGER DEFAULT 0"),
                ("comments", "INTEGER DEFAULT 0"),
                ("shares", "INTEGER DEFAULT 0"),
                ("scheduled_time", "TEXT DEFAULT ''"),
                ("last_tracked_at", "DATETIME"),
                ("account_persona_id", "VARCHAR(50) DEFAULT ''"),
                ("is_viral", "BOOLEAN DEFAULT 0"),
                ("viral_criteria_views", "INTEGER DEFAULT 1000"),
                ("viral_alert_sent", "BOOLEAN DEFAULT 0"),
                ("viral_notified_at", "DATETIME"),
            ]
            for col_name, col_def in clip_cols:
                if col_name not in existing_clip_cols:
                    cur.execute(f"ALTER TABLE clips ADD COLUMN {col_name} {col_def}")

            # Check social_accounts columns
            cur.execute("PRAGMA table_info(social_accounts)")
            existing_acc_cols = {row[1] for row in cur.fetchall()}
            acc_cols = [
                ("channel_name", "VARCHAR(120) DEFAULT ''"),
                ("channel_id", "VARCHAR(120) DEFAULT ''"),
                ("follower_count", "INTEGER DEFAULT 0"),
            ]
            for col_name, col_def in acc_cols:
                if col_name not in existing_acc_cols:
                    cur.execute(f"ALTER TABLE social_accounts ADD COLUMN {col_name} {col_def}")

            # Check account_personas columns
            cur.execute("PRAGMA table_info(account_personas)")
            existing_persona_cols = {row[1] for row in cur.fetchall()}
            persona_cols = [
                ("gmail", "VARCHAR(120) DEFAULT ''"),
                ("content_type", "VARCHAR(50) DEFAULT 'whop_content'"),
            ]
            for col_name, col_def in persona_cols:
                if col_name not in existing_persona_cols:
                    cur.execute(f"ALTER TABLE account_personas ADD COLUMN {col_name} {col_def}")

            conn.commit()
            conn.close()

            # Seed default AccountPersona and SystemSetting if missing
            first_user = User.query.first()
            if first_user:
                # Seed system settings if missing
                setting_keys = {
                    "viral_views_criteria": "1000",
                    "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
                    "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
                }
                for k, v in setting_keys.items():
                    existing_s = SystemSetting.query.filter_by(user_id=first_user.id, key=k).first()
                    if not existing_s:
                        db.session.add(SystemSetting(user_id=first_user.id, key=k, value=v))

                db.session.commit()

        except Exception as e:
            print(f"[DB] Migration notice: {e}")


def authenticate_credentials(username: str, password: str) -> bool:
    """
    Validates credentials against database users and flowchart password requirement.
    Matches Flowchart Node: 'create a USERNAME and password must be: Booma@07'
    """
    from web_app.app import bcrypt
    if not username or not password:
        return False
    
    migrate_db()

    # Check against database
    clean_user = username.strip().lower()
    email_candidate = clean_user if "@" in clean_user else f"{clean_user}@goingmerry.ai"
    user = User.query.filter(
        (User.username == clean_user) | 
        (User.email == clean_user) | 
        (User.email == email_candidate)
    ).first()
    
    if user:
        if bcrypt.check_password_hash(user.password_hash, password):
            return True
        # Flowchart rule: If master password Booma@07 is provided, sync password and authenticate
        if password == "Booma@07":
            user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            try:
                db.session.commit()
                return True
            except Exception:
                db.session.rollback()
                return False
        return False

    # New user: If password is Booma@07, automatically create and authenticate
    if password == "Booma@07":
        pw_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        actual_email = email_candidate
        if User.query.filter_by(email=actual_email).first():
            import time
            actual_email = f"{clean_user}_{int(time.time())}@goingmerry.ai"
        new_user = User(username=clean_user, email=actual_email, password_hash=pw_hash)
        db.session.add(new_user)
        try:
            db.session.commit()
            print(f"[AUTH] Flowchart user '{clean_user}' created and authenticated.")
            return True
        except Exception:
            db.session.rollback()
            return False

    return False
