""" Social account routes — connect/disconnect platforms """
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from web_app.app import db
from web_app.models import SocialAccount
from clipper.core.postiz_manager import PostizManager

social_bp = Blueprint("social", __name__)


@social_bp.route("/social")
@login_required
def social_home():
    postiz = PostizManager()
    health = postiz.check_health()
    integrations = postiz.get_integrations() if health.get("online") else []
    accounts = SocialAccount.query.filter_by(user_id=current_user.id).all()
    
    # Also load local multi-account profiles
    from clipper.uploader.profiles_manager import ProfileManager
    local_accounts = ProfileManager().list_accounts()

    return render_template(
        "social.html",
        accounts=accounts,
        postiz_health=health,
        integrations=integrations,
        postiz_url=postiz.api_url,
        local_accounts=local_accounts
    )

