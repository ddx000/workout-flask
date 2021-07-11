
import os
import json
import requests
import sqlite3

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


from flask import Flask, redirect, request, url_for, jsonify, render_template
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

# Internal imports
from db import init_db_command
from user import User


with open("key.json", "r") as f:
    key = json.load(f)
    GOOGLE_OAUTH2_CLIENT_ID = key["GOOGLE_OAUTH2_CLIENT_ID"]


app = Flask(__name__)
app.secret_key = os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


@app.route("/")
def index():
    return render_template('index.html', google_oauth2_client_id=GOOGLE_OAUTH2_CLIENT_ID)


# @app.route('/login')
# def login_oauth():
#     print("login_oauth")
#     return render_template('index.html', google_oauth2_client_id=GOOGLE_OAUTH2_CLIENT_ID)


@app.route('/google_sign_in', methods=['POST'])
def google_sign_in():
    # frontend user authorized and send a token(authtoken) here
    token = request.json['id_token']
    try:
        id_info = id_token.verify_oauth2_token(
            token,
            google_requests.Request(),
            GOOGLE_OAUTH2_CLIENT_ID
        )
        # use this token and client_id to get more detailed info in backend

        print(id_info)
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')

        create_user_by_googleoauth(id_info)

    except ValueError:
        # Invalid token
        raise ValueError('Invalid token')
    print('登入成功')

    return jsonify({}), 200


def create_user_by_googleoauth(userinfo_response):
    if userinfo_response.get("email_verified"):
        unique_id = userinfo_response["sub"]
        users_email = userinfo_response["email"]
        picture = userinfo_response["picture"]
        users_name = userinfo_response["given_name"]
    else:
        print("User email not available or not verified by Google.")

    # create a model
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)
    print("login!!!!!!!!!!!!!!!")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


app.run(debug=True)
