
import jwt
import requests
from flask import Blueprint, redirect, request, session, url_for
from CTFd.models import Users, db
from CTFd.utils import get_config
from CTFd.utils.logging import log

supabase_sso = Blueprint("supabase_sso", __name__)

SUPABASE_URL = "https://nxbvkoltbuowearddemd.supabase.co"
SUPABASE_JWT_SECRET = "TON_LEGACY_JWT_SECRET_ICI"

def load(app):
    app.register_blueprint(supabase_sso)
    log("supabase_sso", "Supabase SSO plugin loaded")


@supabase_sso.route("/sso/supabase", methods=["GET"])
def supabase_login():
    token = request.args.get("token")

    if not token:
        return redirect("/login?error=missing_token")

    try:
        # Vérifie et décode le JWT Supabase
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}
        )
    except jwt.ExpiredSignatureError:
        return redirect("/login?error=token_expired")
    except jwt.InvalidTokenError as e:
        log("supabase_sso", f"Invalid token: {e}")
        return redirect("/login?error=invalid_token")

    email = payload.get("email")
    user_id = payload.get("sub")

    if not email:
        return redirect("/login?error=no_email")

    # Cherche l'utilisateur existant
    user = Users.query.filter_by(email=email).first()

    if not user:
        # Crée l'utilisateur automatiquement
        username = email.split("@")[0]
        # Évite les doublons de username
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

    # Connecte l'utilisateur
    session["id"] = user.id
    session["nonce"] = user.password  # nonce CTFd

    log("supabase_sso", f"SSO login: {email}")
    return redirect("/")
