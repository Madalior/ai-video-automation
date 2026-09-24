""" Auth routes — signup, login, logout """
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from web_app.app import db, bcrypt
from web_app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dash.dashboard"))
    return redirect(url_for("auth.login"))


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    # Single-operator console — signup redirects to passcode login
    return redirect(url_for("auth.login"))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dash.dashboard"))

    if request.method == "POST":
        passcode = (
            request.form.get("passcode", "") or 
            request.form.get("password", "")
        ).strip()

        if passcode == "Booma@07":
            # Master Operator Authenticated
            master_user = User.query.first()
            if not master_user:
                pw_hash = bcrypt.generate_password_hash("Booma@07").decode("utf-8")
                master_user = User(username="captain", email="captain@goingmerry.ai", password_hash=pw_hash)
                db.session.add(master_user)
                db.session.commit()

            login_user(master_user, remember=True)
            flash("Welcome to Command Center! 🚢", "success")
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dash.dashboard"))
        else:
            flash("passcode is wrong daa", "error")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You've left the ship. See you soon! 👋", "info")
    return redirect(url_for("auth.login"))
