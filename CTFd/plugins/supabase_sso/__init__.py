import os
import requests
from flask import Blueprint, redirect, request, session
from CTFd.models import Users, db
from CTFd.utils.logging import log

supabase_sso = Blueprint("supabase_sso", __name__)

SUPABASE_URL = "https://nxbvkoltbuowearddemd.supabase.co"
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")

def load(app):
    app.register_blueprint(supabase_sso)
    print("[supabase_sso] Supabase SSO plugin loaded")

@supabase_sso.route("/sso/supabase", methods=["GET"])
def supabase_login():
    token = request.args.get("token")
    print(f"[SSO] Token reçu: {token[:20] if token else 'None'}...")

    if not token:
        return redirect("/login?error=missing_token")

    print(f"[SSO] ANON_KEY: {SUPABASE_ANON_KEY[:10] if SUPABASE_ANON_KEY else 'NOT SET'}...")

    resp = requests.get(
        f"{SUPABASE_URL}/auth/v1/user",
        headers={
            "Authorization": f"Bearer {token}",
            "apikey": SUPABASE_ANON_KEY
        }
    )

    print(f"[SSO] Supabase response: {resp.status_code} — {resp.text[:200]}")

    if resp.status_code != 200:
        log("supabase_sso", f"Token validation failed: {resp.status_code}")
        return redirect("/login?error=invalid_token")

    user_data = resp.json()
    email = user_data.get("email")
    user_id = user_data.get("id")

    if not email:
        return redirect("/login?error=no_email")

    # Cherche ou crée l'utilisateur CTFd
    user = Users.query.filter_by(email=email).first()

    if not user:
        username = email.split("@")[0]
        base = username
        counter = 1
        while Users.query.filter_by(name=username).first():
            username = f"{base}{counter}"
            counter += 1

        user = Users(
            name=username,
            email=email,
            verified=True,
            oauth_id=user_id
        )
        db.session.add(user)
        db.session.commit()
        log("supabase_sso", f"Created user {email}")

    session["id"] = user.id
    session["nonce"] = user.password

    log("supabase_sso", f"SSO login: {email}")
    return redirect("/")
