import os
import requests
from flask import Blueprint, redirect, request, session
from CTFd.models import Users, db
from CTFd.utils.logging import log
from CTFd.utils.user import get_current_user

supabase_sso = Blueprint("supabase_sso", __name__)

SUPABASE_URL = os.environ.get("SUPABASE_LEARN_URL", "https://jxeytuqzrymtmekqvpvg.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_LEARN_ANON_KEY")
ADMIN_SECRET = os.environ.get("ADMIN_LOGIN_SECRET", "85lzedlgvFYoxtTM1gwvnuO#g1pWSBS4FjPP+mVVguk3VnNLryUdRz5bIQzXfQVguo9fDSiTTUHnY81FtIjIkw==")


def load(app):
    app.register_blueprint(supabase_sso)

    # Override les routes natives CTFd
    app.view_functions["auth.login"] = redirect_login
    app.view_functions["auth.register"] = redirect_register


@supabase_sso.route("/login", methods=["GET"])
def redirect_login():
    if get_current_user():
        return redirect("/")
    if request.args.get("secret") == ADMIN_SECRET:
        return redirect("/admin-native-login")
    return redirect("https://soopha-learn.com/pages/dashboard.html")


@supabase_sso.route("/register", methods=["GET", "POST"])
def redirect_register():
    return redirect("https://soopha-learn.com/pages/dashboard.html")


@supabase_sso.route("/admin-native-login", methods=["GET", "POST"])
def admin_native_login():
    from CTFd.auth import login as ctfd_login
    return ctfd_login()


@supabase_sso.route("/sso/supabase", methods=["GET"])
def supabase_login():
    token = request.args.get("token")

    if not token:
        return redirect("/login?error=missing_token")

    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY
        }
    )

    if resp.status_code != 200:
        return redirect("/login?error=invalid_token")

    user_data = resp.json()
    email = user_data.get("email")

    if not email:
        return redirect("/login?error=no_email")

    user = Users.query.filter_by(email=email).first()

    if not user:
        username = email.split("@")[0]
        base = username
        counter = 1
        while Users.query.filter_by(name=username).first():
            username = f"{base}{counter}"
            counter += 1
        try:
            db.session.rollback()
            user = Users(name=username, email=email, verified=True)
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return redirect("/login?error=creation_failed")

    session["id"] = user.id
    session["nonce"] = user.password
    log("supabase_sso", f"SSO login: {email}")
    return redirect("/")
