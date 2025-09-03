from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, UserMixin
from werkzeug.security import check_password_hash
from .models import db, User

auth_bp = Blueprint("auth", __name__)
login_manager = LoginManager()
login_manager.login_view = "auth.login"

class LoginUser(UserMixin):
    def __init__(self, model):
        self.id = model.id; self.username = model.username; self.role = model.role

@login_manager.user_loader
def load_user(user_id):
    u = User.query.get(int(user_id))
    return LoginUser(u) if u else None

@auth_bp.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        u = User.query.filter_by(username=username).first()
        if u and check_password_hash(u.password_hash, password):
            login_user(LoginUser(u))
            return redirect(request.args.get("next") or url_for("pages.home"))
        flash("Credenciais inválidas.", "error")
    return render_template("login.html")

@auth_bp.get("/logout")
def logout():
    logout_user()
    return redirect(url_for("pages.home"))
