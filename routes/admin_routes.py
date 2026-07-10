from flask import Blueprint, render_template, session, redirect, request, flash

from modules.auth_service import auth_service
from database import db
from datetime import datetime

admin_bp = Blueprint(
    "admin",
    __name__
)


@admin_bp.route("/admin")
def dashboard():

    if session.get("role") != "Admin":
        return redirect("/login")
    
    total_users = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM users
        """)["total"]

    total_citizens = db.fetchone(
        "SELECT COUNT(*) AS total FROM users WHERE role='Citizen'"
    )["total"]

    total_police = db.fetchone(
        "SELECT COUNT(*) AS total FROM users WHERE role='Police'"
    )["total"]

    total_reports = db.fetchone(
        "SELECT COUNT(*) AS total FROM crime_reports"
    )["total"]

    pending_cases = db.fetchone(
        """
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE status='Pending'
        """
    )["total"]

    fir = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE status='FIR Registered'
        """)["total"]
    
    investigation = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE status='Under Investigation'
        """)["total"]
    
    rejected = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE status='Rejected'
        """)["total"]
    
    closed = db.fetchone("""
        SELECT COUNT(*) AS total
        FROM crime_reports
        WHERE status IN ('Resolved','Closed')
        """)["total"]

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_citizens=total_citizens,
        total_police=total_police,
        total_reports=total_reports,
        investigation=investigation,
        fir=fir,
        rejected=rejected,
        closed=closed,
        pending_cases=pending_cases
    )

@admin_bp.route("/admin/police")
def police():

    if session.get("role") != "Admin":
        return redirect("/login")

    police = db.fetchall(
        """
        SELECT
            user_id,
            full_name,
            username,
            phone,
            address
        FROM users
        WHERE role='Police'
        ORDER BY full_name
        """
    )

    return render_template(
        "admin/police.html",
        police=police
    )

@admin_bp.route("/admin/police/add", methods=["GET", "POST"])
def add_police():

    if session.get("role") != "Admin":
        return redirect("/login")

    if request.method == "POST":

        full_name = request.form["full_name"]
        username = request.form["username"]
        password = request.form["password"]
        phone = request.form["phone"]
        address = request.form["address"]

        success, message = auth_service.create_police(
            full_name,
            username,
            password,
            phone,
            address
        )

        flash(message)

        if success:
            return redirect("/admin/police")
        
    return render_template("admin/add_police.html")
            


@admin_bp.route("/admin/citizens")
def citizens():

    if session.get("role") != "Admin":
        return redirect("/login")

    citizens = db.fetchall(
        """
        SELECT
            user_id,
            full_name,
            username,
            phone,
            address
        FROM users
        WHERE role='Citizen'
        ORDER BY full_name
        """
    )

    return render_template(
        "admin/citizens.html",
        citizens=citizens
    )

@admin_bp.route("/admin/reports")
def reports():

    if session.get("role") != "Admin":
        return redirect("/login")

    reports = db.fetchall(
        """
        SELECT
            cr.report_id,
            u.full_name,
            c.category_name,
            cr.title,
            cr.location,
            cr.report_date,
            cr.status
        FROM crime_reports cr

        JOIN users u
            ON cr.citizen_id = u.user_id

        LEFT JOIN crime_categories c
            ON cr.category_id = c.category_id

        ORDER BY cr.report_date DESC
        """
    )

    return render_template(
        "admin/reports.html",
        reports=reports
    )

@admin_bp.route("/admin/reports/<int:report_id>")
def report_details(report_id):

    if session.get("role") != "Admin":
        return redirect("/login")

    report = db.fetchone("""
        SELECT
            cr.*,
            citizen.full_name AS citizen_name,
            c.category_name,
            officer.full_name AS officer_name,
            f.fir_number,
            f.filing_date
        FROM crime_reports cr
        JOIN users citizen
            ON cr.citizen_id = citizen.user_id
        LEFT JOIN crime_categories c
            ON cr.category_id = c.category_id
        LEFT JOIN users officer
            ON cr.assigned_officer = officer.user_id
        LEFT JOIN fir f
            ON cr.report_id = f.report_id
        WHERE cr.report_id=?
        """,
        (report_id,))

    if report is None:
        flash("Crime report not found.")
        return redirect("/admin/reports")

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

        duration = f"{days} days, {hours} hours, {minutes} minutes"
    
    return render_template(
        "admin/report_details.html",
        report=report,
        duration=duration
    )

@admin_bp.route("/admin/feedback")
def feedback():

    if session.get("role") != "Admin":
        return redirect("/login")

    feedbacks = db.fetchall(
        """
        SELECT
            f.feedback_id,
            u.full_name,
            f.message,
            f.feedback_date
        FROM feedback f

        JOIN users u
            ON f.citizen_id = u.user_id

        ORDER BY f.feedback_date DESC
        """
    )
    return render_template(
        "admin/feedback.html",
        feedbacks=feedbacks
    )
