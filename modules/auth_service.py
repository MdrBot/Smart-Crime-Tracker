from database import db
from config import CITIZEN_ROLE
import bcrypt


class AuthService:

    def hash_password(self, password):

        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    def verify_password(self, password, hashed):

        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )

    def register(
        self,
        full_name,
        username,
        password,
        phone,
        address
    ):

        existing = db.fetchone(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        if existing:
            return False, "Username already exists."
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        if not phone.isdigit() or len(phone) != 10:
            return False, "Phone number must contain exactly 10 digits."

        if not address.strip():
            return False, "Address is required."

        hashed = self.hash_password(password)

        db.execute(
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
                full_name,
                username,
                hashed,
                CITIZEN_ROLE,
                phone,
                address
            )
        )

        return True, "Registration successful."

    def login(self, username, password):

        user = db.fetchone(
            """
            SELECT *
            FROM users
            WHERE username = ?
            """,
            (username,)
        )

        if user is None:
            return None

        if not self.verify_password(
            password,
            user["password"]
        ):
            return None

        return user
    
    def create_police(
        self,
        full_name,
        username,
        password,
        phone,
        address
        ):

        existing = db.fetchone(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        if existing:
            return False, "Username already exists."
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters long."

        if not phone.isdigit() or len(phone) != 10:
            return False, "Phone number must contain exactly 10 digits."

        if not address.strip():
            return False, "Address is required."

        hashed = self.hash_password(password)

        db.execute(
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
                full_name,
                username,
                hashed,
                "Police",
                phone,
                address
            )
        )

        return True, "Police officer added successfully."


auth_service = AuthService()