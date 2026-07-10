from flask import Blueprint, render_template, session, redirect, flash, request
from database import db
from datetime import datetime
from modules.auth_service import auth_service

police_bp = Blueprint(
    "police",
    __name__
)


@police_bp.route("/police")
def dashboard():

    if session.get("role") != "Police":
        return redirect("/login")

    officer_id = session["user_id"]

    pending_reports = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE assigned_officer IS NULL
        AND status='Pending'
        """)["total"]

    fir_registered = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE assigned_officer=?
        AND status='FIR Registered'
        """,
        (officer_id,)
    )["total"]

    rejected = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE assigned_officer=?
        AND status='Rejected'
        """,
        (session["user_id"],)
        )["total"] 

    investigating = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE assigned_officer=?
        AND status='Under Investigation'
        """,
        (officer_id,)
    )["total"]

    closed = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE assigned_officer=?
        AND status IN ('Resolved','Closed')
        """,
        (officer_id,)
    )["total"]

    return render_template(
        "police/dashboard.html",
        pending_reports=pending_reports,
        fir_registered=fir_registered,
        investigating=investigating,
        rejected=rejected,
        closed=closed
    )

@police_bp.route("/police/pending")
def pending_reports():

    if session.get("role") != "Police":
        return redirect("/login")

    reports = db.fetchall("""
        SELECT
            cr.report_id,
            cc.category_name,
            cr.title,
            u.full_name AS citizen_name,
            cr.incident_date,
            cr.location,
            cr.status
        FROM crime_reports cr
        JOIN users u
            ON cr.citizen_id = u.user_id
        JOIN crime_categories cc
            ON cr.category_id = cc.category_id
        WHERE cr.assigned_officer IS NULL
        AND cr.status='Pending'
        ORDER BY cr.report_date DESC
    """)

    return render_template(
        "police/pending_reports.html",
        reports=reports
    )


@police_bp.route("/police/report/<int:report_id>")
def report_details(report_id):

    if session.get("role") != "Police":
        return redirect("/login")

    report = db.fetchone("""
        SELECT
            cr.*,
            u.full_name,
            u.phone,
            u.address,
            cc.category_name
        FROM crime_reports cr

        JOIN users u
            ON cr.citizen_id=u.user_id

        JOIN crime_categories cc
            ON cr.category_id=cc.category_id

        WHERE report_id=?
    """, (report_id,))

    if report is None:
        flash("Report not found.")
        return redirect("/police/pending")
    
    if report["assigned_officer"] is not None and \
        report["assigned_officer"] != session["user_id"]:

        flash("This case is assigned to another officer.")

        return redirect("/police")

    duration = None

    if report["created_at"] and report["closed_at"]:

        start = datetime.strptime(
            report["created_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        end = datetime.strptime(
            report["closed_at"],
            "%Y-%m-%d %H:%M:%S"
        )

        diff = end - start

        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60

        duration = f"{days} day(s), {hours} hour(s), {minutes} minute(s)"
    
    return render_template(
        "police/report_details.html",
        report=report,
        duration=duration
    )

@police_bp.route("/police/report/<int:report_id>/register-fir")
def register_fir(report_id):

    if session.get("role") != "Police":
        return redirect("/login")

    # Check whether an FIR already exists
    existing = db.fetchone("""
        SELECT fir_id
        FROM fir
        WHERE report_id=?
    """, (report_id,))

    if existing:
        flash("FIR has already been registered.")
        return redirect(f"/police/report/{report_id}")

    # Generate FIR Number
    fir_number = "FIR-" + datetime.now().strftime("%Y%m%d%H%M%S")

    # Assign officer and update report status
    db.execute("""
        UPDATE crime_reports
        SET
            assigned_officer=?,
            status='FIR Registered'
        WHERE report_id=?
    """,
    (
        session["user_id"],
        report_id
    ))

    # Create FIR
    db.execute("""
        INSERT INTO fir
        (
            report_id,
            fir_number,
            registered_by,
            filing_date,
            remarks,
            status
        )
        VALUES
        (
            ?, ?, ?, datetime('now','localtime'), ?, 'Registered'
        )
    """,
    (
        report_id,
        fir_number,
        session["user_id"],
        "FIR Registered"
    ))

    flash("FIR registered successfully.")

    return redirect(f"/police/report/{report_id}")

@police_bp.route("/police/report/<int:report_id>/reject",
                 methods=["GET", "POST"])
def reject_report(report_id):

    if session.get("role") != "Police":
        return redirect("/login")

    if request.method == "POST":

        reason = request.form["reason"]

        db.execute("""
            UPDATE crime_reports

            SET
                status='Rejected',
                rejection_reason=?

            WHERE report_id=?
        """,
        (
            reason,
            report_id
        ))

        flash("Report rejected as Non-Cognizable.")

        return redirect("/police")

    return render_template(
        "police/reject_report.html",
        report_id=report_id
    )



@police_bp.route("/police/my-cases")
def assigned_cases():

    if session.get("role") != "Police":
        return redirect("/login")

    reports = db.fetchall("""
        SELECT
            cr.report_id,
            cc.category_name,
            cr.title,
            cr.location,
            cr.incident_date,
            cr.status
        FROM crime_reports cr

        JOIN crime_categories cc
            ON cr.category_id = cc.category_id

        WHERE cr.assigned_officer = ?

        ORDER BY cr.report_date DESC
    """,
    (session["user_id"],)
    )

    return render_template(
        "police/my_cases.html",
        reports=reports
    )

@police_bp.route("/police/profile")
def profile():

    if session.get("role") != "Police":
        return redirect("/login")

    officer = db.fetchone("""
        SELECT
            full_name,
            username,
            phone,
            address
        FROM users
        WHERE user_id=?
    """,
    (session["user_id"],)
    )

    return render_template(
        "police/profile.html",
        officer=officer
    )

@police_bp.route("/police/profile/edit", methods=["GET", "POST"])
def edit_profile():

    if session.get("role") != "Police":
        return redirect("/login")

    if request.method == "POST":

        db.execute("""
            UPDATE users
            SET
                full_name=?,
                phone=?,
                address=?
            WHERE user_id=?
        """,
        (
            request.form["full_name"],
            request.form["phone"],
            request.form["address"],
            session["user_id"]
        ))

        flash("Profile updated successfully.")

        return redirect("/police/profile")

    officer = db.fetchone(
        "SELECT * FROM users WHERE user_id=?",
        (session["user_id"],)
    )

    return render_template(
        "police/edit_profile.html",
        officer=officer
    )

@police_bp.route("/police/change-password", methods=["GET", "POST"])
def change_password():

    if session.get("role") != "Police":
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
            return redirect("/police/change-password")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return redirect("/police/change-password")

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

        return redirect("/police/profile")

    return render_template("police/change_password.html")

@police_bp.route("/police/report/<int:report_id>/status", methods=["POST"])
def update_status(report_id):

    if session.get("role") != "Police":
        return redirect("/login")

    new_status = request.form["status"]
    closing_remarks = request.form.get("closing_remarks", "")
    if new_status == "Closed" and not closing_remarks.strip():

        flash("Please provide closing remarks before closing the case.")

        return redirect(f"/police/report/{report_id}")

    if new_status == "Closed":

        db.execute("""
            UPDATE crime_reports

            SET
            status=?,
            closed_at=datetime('now','localtime'),
            closing_remarks=?

            WHERE report_id=?
            AND assigned_officer=?
            """,
        (
        new_status,
        closing_remarks,
        report_id,
        session["user_id"]
        ))

    else:

        db.execute("""
            UPDATE crime_reports

            SET status=?

            WHERE report_id=?
            AND assigned_officer=?
        """,
        (
            new_status,
            report_id,
            session["user_id"]
        ))

    flash("Case status updated successfully.")

    return redirect(f"/police/report/{report_id}")