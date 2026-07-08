from flask import Blueprint, render_template, session, redirect, request, flash
from database import db
from modules.auth_service import auth_service

citizen_bp = Blueprint(
    "citizen",
    __name__
)


@citizen_bp.route("/citizen")
def dashboard():

    if session.get("role") != "Citizen":
        return redirect("/login")

    user_id = session["user_id"]

    total_reports = db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id = ?
        """,
        (user_id,)
    )["total"]

    pending_reports = db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id = ?
        AND status = 'Pending'
        """,
        (user_id,)
    )["total"]

    fir_registered = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id=?
        AND status='FIR Registered'
        """,
        (session["user_id"],)
    )["total"]

    rejected = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id=?
        AND status='Rejected'
        """,
        (session["user_id"],)
    )["total"]

    investigating = db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id = ?
        AND status = 'Under Investigation'
        """,
        (user_id,)
    )["total"]

    closed = db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE citizen_id = ?
        AND status IN ('Resolved','Closed')
        """,
        (user_id,)
    )["total"]

    return render_template(
        "citizen/dashboard.html",
        total_reports=total_reports,
        pending_reports=pending_reports,
        fir_registered=fir_registered,
        rejected=rejected,
        investigating=investigating,
        closed=closed
    )



@citizen_bp.route("/citizen/reports")
def my_reports():

    if session.get("role") != "Citizen":
        return redirect("/login")

    reports = db.fetchall(
        """
        SELECT
            cr.report_id,
            cc.category_name,
            cr.title,
            cr.report_date,
            cr.status
        FROM crime_reports cr

        LEFT JOIN crime_categories cc
            ON cr.category_id = cc.category_id

        WHERE cr.citizen_id = ?

        ORDER BY cr.report_date DESC
        """,
        (session["user_id"],)
    )

    return render_template(
        "citizen/my_reports.html",
        reports=reports
    )


@citizen_bp.route("/citizen/report", methods=["GET", "POST"])
def report_crime():

    if session.get("role") != "Citizen":
        return redirect("/login")

    categories = db.fetchall(
        """
        SELECT
            category_id,
            category_name
        FROM crime_categories
        ORDER BY category_id
        """
    )

    if request.method == "POST":

        citizen_id = session["user_id"]

        category_id = request.form["category_id"]
        title = request.form["title"].strip()
        description = request.form["description"].strip()
        location = request.form["location"].strip()
        incident_date = request.form["incident_date"]

        db.execute(
            """
            INSERT INTO crime_reports
            (
                citizen_id,
                category_id,
                title,
                description,
                location,
                incident_date,
                report_date,
                status
            )

            VALUES
            (
                ?, ?, ?, ?, ?, ?, datetime('now'), 'Pending'
            )
            """,
            (
                citizen_id,
                category_id,
                title,
                description,
                location,
                incident_date
            )
        )

        flash("Crime report submitted successfully.")

        return redirect("/citizen/reports")

    return render_template(
        "citizen/report_crime.html",
        categories=categories
    )

@citizen_bp.route("/citizen/reports/<int:report_id>")
def report_details(report_id):

    if session.get("role") != "Citizen":
        return redirect("/login")

    report = db.fetchone(
        """
        SELECT
            cr.*,
            cc.category_name
        FROM crime_reports cr

        LEFT JOIN crime_categories cc
            ON cr.category_id = cc.category_id

        WHERE cr.report_id = ?
        AND cr.citizen_id = ?
        """,
        (
            report_id,
            session["user_id"]
        )
    )

    if report is None:

        flash("Report not found.")

        return redirect("/citizen/reports")

    return render_template(
        "citizen/report_details.html",
        report=report
    )

@citizen_bp.route("/citizen/profile", methods=["GET", "POST"])
def profile():

    if session.get("role") != "Citizen":
        return redirect("/login")

    user = db.fetchone(
        """
        SELECT *
        FROM users
        WHERE user_id = ?
        """,
        (session["user_id"],)
    )

    if request.method == "POST":

        full_name = request.form["full_name"].strip()
        phone = request.form["phone"].strip()
        address = request.form["address"].strip()

        db.execute(
            """
            UPDATE users
            SET
                full_name = ?,
                phone = ?,
                address = ?
            WHERE user_id = ?
            """,
            (
                full_name,
                phone,
                address,
                session["user_id"]
            )
        )

        session["full_name"] = full_name

        flash("Profile updated successfully.")

        return redirect("/citizen/profile")

    return render_template(
        "citizen/profile.html",
        user=user
    )

@citizen_bp.route("/citizen/change-password", methods=["GET", "POST"])
def change_password():

    if session.get("role") != "Citizen":
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        user = db.fetchone(
            """
            SELECT *
            FROM users
            WHERE user_id=?
            """,
            (session["user_id"],)
        )

        if not auth_service.verify_password(
            current_password,
            user["password"]
        ):
            flash("Current password is incorrect.")
            return redirect("/citizen/change-password")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/citizen/change-password")

        hashed = auth_service.hash_password(new_password)

        db.execute(
            """
            UPDATE users
            SET password=?
            WHERE user_id=?
            """,
            (
                hashed,
                session["user_id"]
            )
        )

        flash("Password changed successfully.")

        return redirect("/citizen/profile")

    return render_template("citizen/change_password.html")

@citizen_bp.route("/citizen/feedback", methods=["GET", "POST"])
def feedback():

    if session.get("role") != "Citizen":
        return redirect("/login")

    # Check if this user has already submitted feedback
    existing_feedback = db.fetchone("""
        SELECT *
        FROM feedback
        WHERE user_id=?
    """,
    (session["user_id"],))

    if request.method == "POST":

        # Prevent duplicate feedback
        if existing_feedback:
            flash("You have already submitted feedback.")
            return redirect("/citizen/feedback")

        message = request.form["message"]

        db.execute("""
            INSERT INTO feedback
            (
                user_id,
                message,
                feedback_date
            )
            VALUES
            (
                ?, ?, datetime('now')
            )
        """,
        (
            session["user_id"],
            message
        ))

        flash("Feedback submitted successfully.")

        return redirect("/citizen/feedback")

    return render_template(
        "citizen/feedback.html",
        feedback=existing_feedback
    )

@citizen_bp.route("/citizen/feedback/edit", methods=["GET", "POST"])
def edit_feedback():

    if session.get("role") != "Citizen":
        return redirect("/login")

    if request.method == "POST":

        message = request.form["message"]

        db.execute("""
        UPDATE feedback

        SET message=?

        WHERE user_id=?
        """,
        (
            message,
            session["user_id"]
        ))

        flash("Feedback updated successfully.")

        return redirect("/citizen/feedback")

    feedback = db.fetchone("""
    SELECT *
    FROM feedback
    WHERE user_id=?
    """,
    (session["user_id"],))

    return render_template(
        "citizen/edit_feedback.html",
        feedback=feedback
    )

@citizen_bp.route("/citizen/feedback/delete")
def delete_feedback():

    if session.get("role") != "Citizen":
        return redirect("/login")

    db.execute("""
    DELETE FROM feedback

    WHERE user_id=?
    """,
    (session["user_id"],))

    flash("Feedback deleted successfully.")

    return redirect("/citizen/feedback")