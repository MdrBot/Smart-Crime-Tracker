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