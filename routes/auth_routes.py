from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from modules.auth_service import auth_service
import re



auth_bp = Blueprint(
    "auth",
    __name__
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login_page():

    if request.method == "POST":

        username = request.form["username"].strip()
        password = request.form["password"]

        user = auth_service.login(username, password)

        if user is None:
            flash("Invalid username or password.")
            return render_template("login.html")

        session["user_id"] = user["user_id"]
        session["role"] = user["role"]
        session["full_name"] = user["full_name"]

        flash("Login Successful.")

        if user["role"] == "Admin":
            return redirect("/admin")

        elif user["role"] == "Police":
            return redirect("/police")

        else:
            return redirect("/citizen")

    return render_template("login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        username = request.form["username"].strip()
        password = request.form["password"]
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()

        # Full Name validation
        if not full_name:
            flash("Full Name is required.")
            return render_template("register.html")

        if full_name.isdigit():
            flash("Full Name cannot contain only numbers.")
            return render_template("register.html")

        if not re.fullmatch(r"[A-Za-z ]+", full_name):
            flash("Full Name can contain only letters and spaces.")
            return render_template("register.html")

        # Username validation
        if not username:
            flash("Username is required.")
            return render_template("register.html")

        if username.isdigit():
            flash("Username cannot contain only numbers.")
            return render_template("register.html")

        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", username):
            flash("Username must start with a letter and contain only letters, numbers, and underscores.")
            return render_template("register.html")
        
        # Password validation
        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return render_template("register.html")

        if not re.search(r"[A-Z]", password):
            flash("Password must contain at least one uppercase letter.")
            return render_template("register.html")

        if not re.search(r"[0-9]", password):
            flash("Password must contain at least one number.")
            return render_template("register.html")

        success, message = auth_service.register(
            full_name,
            username,
            password,
            phone,
            address
        )

        flash(message)

        if success:
            return redirect(url_for("auth.login_page"))

    return render_template("register.html")

@auth_bp.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully.")

    return redirect(url_for("auth.login_page"))