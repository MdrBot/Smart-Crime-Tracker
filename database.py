import sqlite3
from config import DATABASE_PATH
import bcrypt

print("Database path:", DATABASE_PATH)

class Database:

    def __init__(self):

        self.connection = sqlite3.connect(
            DATABASE_PATH,
            check_same_thread=False
        )

        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()

        self.create_tables()
        self.create_default_admin()
        self.connection.commit()

    # Generic Database Methods

    def execute(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        self.connection.commit()

    def fetchone(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        return self.cursor.fetchone()

    def fetchall(self, query, parameters=()):
        self.cursor.execute(query, parameters)
        return self.cursor.fetchall()

    def close(self):
        if self.connection:
            self.connection.close()

    # Database Schema

    def create_tables(self):
        """
        Create all tables required for the project.
        """

        # ---------------- USERS ----------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(

            user_id INTEGER PRIMARY KEY AUTOINCREMENT,

            full_name TEXT NOT NULL,

            username TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            role TEXT NOT NULL,

            phone TEXT,

            address TEXT,

            status TEXT DEFAULT 'Active'
        )
        """)

        # ---------------- CRIME CATEGORIES ----------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS crime_categories(

            category_id INTEGER PRIMARY KEY AUTOINCREMENT,

            category_name TEXT UNIQUE NOT NULL

        )
        """)
        default_categories = [
            ("Theft",),
            ("Robbery",),
            ("Traffic Incident",),
            ("Fraud",),
            ("Cyber Crime",),
            ("Domestic Violence",),
            ("Missing Person",),
            ("Vandalism",),
            ("Assault",),
            ("Drug-related Crime",),
            ("Other",)
            ]           

        self.cursor.executemany("""
        INSERT OR IGNORE INTO crime_categories
        (category_name)
        VALUES (?)
        """, default_categories)

        # ---------------- CRIME REPORTS ----------------

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS crime_reports
            (
            report_id INTEGER PRIMARY KEY AUTOINCREMENT,

            citizen_id INTEGER NOT NULL,

            category_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            description TEXT NOT NULL,

            location TEXT NOT NULL,

            incident_date TEXT NOT NULL,

            report_date TEXT NOT NULL,
            
            created_at TEXT,

            closed_at TEXT,

            status TEXT DEFAULT 'Pending Review',

            evidence TEXT,

            FOREIGN KEY(citizen_id)
                REFERENCES users(user_id),

            FOREIGN KEY(category_id)
                REFERENCES crime_categories(category_id)
            )
            """)

        # ---------------- ONLINE FIR ----------------

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS fir(

            fir_id INTEGER PRIMARY KEY AUTOINCREMENT,

            report_id INTEGER NOT NULL,

            fir_number TEXT UNIQUE NOT NULL,

            registered_by INTEGER NOT NULL,

            filing_date TEXT NOT NULL,

            remarks TEXT,

            status TEXT DEFAULT 'Registered',

            FOREIGN KEY(report_id)
                REFERENCES crime_reports(report_id),

            FOREIGN KEY(registered_by)
                REFERENCES users(user_id)
        )
        """)

        # ---------------- FEEDBACK ----------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback(

            feedback_id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            message TEXT,

            rating INTEGER,

            feedback_date TEXT,

            FOREIGN KEY(user_id)
                REFERENCES users(user_id)
        )
        """)

        # ---------------- AUDIT LOGS ----------------

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs(

            log_id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER,

            action TEXT,

            log_time TEXT,

            FOREIGN KEY(user_id)
                REFERENCES users(user_id)
        )
        """)

        self.connection.commit()

        print("Database initialized successfully.")

    def create_default_admin(self):

        admin = self.fetchone(
            """
            SELECT *
            FROM users
            WHERE role = 'Admin'
            LIMIT 1
            """
        )

        if admin:
            return

        hashed_password = bcrypt.hashpw(
            "admin123".encode(),
            bcrypt.gensalt()
        ).decode()

        self.execute(
            """
            INSERT INTO users
            (
                full_name,
                username,
                password,
                role,
                phone,
                address
            )
            VALUES
            (
                ?, ?, ?, ?, ?, ?
            )
            """,
            (
                "System Administrator",
                "admin",
                hashed_password,
                "Admin",
                "",
                ""
            )
        )

        print("\nDefault administrator account created.")
        print("Username : admin")
        print("Password : admin123")



db = Database()