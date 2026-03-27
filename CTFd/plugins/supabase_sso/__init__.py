import os
import requests
from flask import Blueprint, redirect, request, session
from CTFd.models import Users, db
from CTFd.utils.logging import log

supabase_sso = Blueprint("supabase_sso", __name__)

SUPABASE_URL = os.environ.get("SUPABASE_LEARN_URL", "https://jxeytuqzrymtmekqvpvg.supabase.co")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_LEARN_ANON_KEY")

def load(app):
    app.register_blueprint(supabase_sso)
    

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
            user = Users(
                name=username,
                email=email,
                verified=True
            )
            db.session.add(user)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            return redirect("/login?error=creation_failed")

    session["id"] = user.id
    session["nonce"] = user.password

    log("supabase_sso", f"SSO login: {email}")
    return redirect("/")
