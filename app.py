from flask import Flask, render_template, session
from routes.auth_routes import auth_bp
from routes.admin_routes import admin_bp
from routes.citizen_routes import citizen_bp
from routes.police_routes import police_bp

app = Flask(__name__)

app.secret_key = "smart_crime_tracker_secret_key"

app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(citizen_bp)
app.register_blueprint(police_bp)

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    print("\nRegistered Routes:")
    print(app.url_map)
    app.run(debug=True)