"""
===========================================
Smart Crime Tracker System
Configuration File
===========================================
"""

import os

# -------------------------------
# Project Directories
# -------------------------------

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")

# Create data folder automatically
os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------
# Database
# -------------------------------

DATABASE_NAME = "crime_tracker.db"

DATABASE_PATH = os.path.join(DATA_DIR, DATABASE_NAME)

# -------------------------------
# Application Settings
# -------------------------------

APP_NAME = "Smart Crime Tracker"

VERSION = "1.0"

MAX_LOGIN_ATTEMPTS = 3

DATE_FORMAT = "%Y-%m-%d"

TIME_FORMAT = "%H:%M:%S"

# ==========================================================
# User Roles
# ==========================================================

ADMIN_ROLE = "Admin"
POLICE_ROLE = "Police"
CITIZEN_ROLE = "Citizen"

# ==========================================================
# User Status
# ==========================================================

STATUS_ACTIVE = "Active"
STATUS_INACTIVE = "Inactive"

# ==========================================================
# Crime Report Status
# ==========================================================

REPORT_PENDING = "Pending"
REPORT_UNDER_INVESTIGATION = "Under Investigation"
REPORT_RESOLVED = "Resolved"
REPORT_REJECTED = "Rejected"