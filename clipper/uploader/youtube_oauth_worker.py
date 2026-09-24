"""
YouTube OAuth Worker
====================
Standalone process to perform Google OAuth2 authorization for a specific account.
Opens the browser for Google consent, receives tokens via local redirect server,
queries the YouTube Data API for actual channel info, and saves credentials.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCOPES = [
    'https://www.googleapis.com/auth/youtube.upload',
    'https://www.googleapis.com/auth/youtube'
]


def authenticate_account(account_id: str, client_secrets_path: Path, tokens_dir: Path):
    tokens_dir.mkdir(parents=True, exist_ok=True)
    token_file = tokens_dir / f"token_{account_id}.json"
    channel_file = tokens_dir / f"channel_{account_id}.json"
    status_file = tokens_dir / f"status_{account_id}.json"

    # Write initial progress
    with open(status_file, "w", encoding="utf-8") as f:
        json.dump({"status": "starting", "message": "Opening Google authorization page in your browser..."}, f)

    if not client_secrets_path.exists():
        err_msg = f"client_secrets.json not found at {client_secrets_path}"
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump({"status": "error", "message": err_msg}, f)
        print(json.dumps({"success": False, "error": err_msg}))
        return False

    try:
        import wsgiref.simple_server
        from google_auth_oauthlib.flow import InstalledAppFlow, _RedirectWSGIApp, _WSGIRequestHandler
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials

        flow = InstalledAppFlow.from_client_secrets_file(
            str(client_secrets_path),
            SCOPES
        )

        success_html = """
        <html>
        <head><title>Going Merry - YouTube Connected</title>
        <style>body{font-family:sans-serif;background:#111;color:#4CE616;display:flex;align-items:center;justify-content:center;height:100vh;margin:0;}
        .box{border:2px solid #4CE616;padding:40px;text-align:center;border-radius:12px;box-shadow:0 0 30px rgba(76,230,22,0.2);}</style>
        </head>
        <body>
        <div class="box">
            <h2>TECHTRONICS / GOING MERRY</h2>
            <h1 style="color:#fff;">YOUTUBE AUTHENTICATED!</h1>
            <p style="color:#aaa;">You can close this tab and return to the console.</p>
        </div>
        </body>
        </html>
        """
        wsgi_app = _RedirectWSGIApp(success_html)
        wsgiref.simple_server.WSGIServer.allow_reuse_address = False
        local_server = wsgiref.simple_server.make_server(
            "localhost", 0, wsgi_app, handler_class=_WSGIRequestHandler
        )
        port = local_server.server_port
        flow.redirect_uri = f"http://localhost:{port}/"

        auth_url, _ = flow.authorization_url(prompt='consent', access_type='offline')

        with open(status_file, "w", encoding="utf-8") as f:
            json.dump({
                "status": "in_progress",
                "auth_url": auth_url,
                "port": port,
                "message": "Browser opened! Please select your Google account and click 'Allow'..."
            }, f, indent=2)

        print(f"[YT_OAUTH] Listening on http://localhost:{port}/")
        print(f"[YT_OAUTH] Authorization URL: {auth_url}")

        # Explicitly launch system browser on Windows
        try:
            os.startfile(auth_url)
        except Exception:
            try:
                import webbrowser
                webbrowser.open(auth_url)
            except Exception:
                pass

        local_server.timeout = 300
        local_server.handle_request()
        local_server.server_close()

        auth_response = wsgi_app.last_request_uri.replace("http://", "https://")
        flow.fetch_token(authorization_response=auth_response)
        creds = flow.credentials

        # Save credentials to token file
        with open(token_file, "w", encoding="utf-8") as f:
            f.write(creds.to_json())

        # Query live YouTube channel details
        youtube = build('youtube', 'v3', credentials=creds)
        channels_res = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()

        items = channels_res.get("items", [])
        if not items:
            channel_info = {
                "title": "YouTube Channel",
                "id": "",
                "custom_url": "",
                "subscriber_count": 0,
                "video_count": 0,
                "thumbnail": ""
            }
        else:
            snippet = items[0].get("snippet", {})
            stats = items[0].get("statistics", {})
            channel_info = {
                "title": snippet.get("title", "YouTube Channel"),
                "id": items[0].get("id", ""),
                "custom_url": snippet.get("customUrl", ""),
                "subscriber_count": int(stats.get("subscriberCount", 0)),
                "video_count": int(stats.get("videoCount", 0)),
                "thumbnail": snippet.get("thumbnails", {}).get("default", {}).get("url", "")
            }

        with open(channel_file, "w", encoding="utf-8") as f:
            json.dump(channel_info, f, indent=2)

        # Update SQLite DB if available
        try:
            from web_app.app import app, db
            from web_app.models import AccountPersona, SocialAccount

            with app.app_context():
                persona = AccountPersona.query.filter_by(id=account_id).first()
                if persona:
                    handle = channel_info.get("custom_url") or f"@{channel_info.get('title')}"
                    persona.youtube_handle = handle
                    persona.youtube_status = "connected"

                    # Also update or create SocialAccount
                    soc = SocialAccount.query.filter_by(user_id=persona.user_id, platform="youtube", channel_id=channel_info["id"]).first()
                    if not soc:
                        soc = SocialAccount(
                            user_id=persona.user_id,
                            platform="youtube",
                            channel_name=channel_info["title"],
                            channel_id=channel_info["id"],
                            follower_count=channel_info["subscriber_count"],
                            is_active=True
                        )
                        db.session.add(soc)
                    else:
                        soc.channel_name = channel_info["title"]
                        soc.follower_count = channel_info["subscriber_count"]
                        soc.is_active = True

                    db.session.commit()
                    print(f"[YT_OAUTH] Updated AccountPersona '{persona.id}' with channel '{channel_info['title']}'")
        except Exception as db_err:
            print(f"[YT_OAUTH] Notice: DB update skipped ({db_err})")

        result = {
            "success": True,
            "status": "connected",
            "account_id": account_id,
            "channel": channel_info,
            "token_path": str(token_file)
        }

        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)

        print(json.dumps(result))
        return True

    except Exception as e:
        err_msg = str(e)
        result = {"success": False, "status": "error", "account_id": account_id, "error": err_msg}
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result))
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube OAuth Account Connector")
    parser.add_argument("--account-id", type=str, default="default", help="Unique account ID (e.g. acc_01)")
    parser.add_argument("--tokens-dir", type=str, default=str(PROJECT_ROOT / "youtube_tokens"), help="Tokens directory")
    parser.add_argument("--secrets", type=str, default=str(PROJECT_ROOT / "client_secrets.json"), help="client_secrets.json path")
    args = parser.parse_args()

    authenticate_account(
        account_id=args.account_id,
        client_secrets_path=Path(args.secrets),
        tokens_dir=Path(args.tokens_dir)
    )
