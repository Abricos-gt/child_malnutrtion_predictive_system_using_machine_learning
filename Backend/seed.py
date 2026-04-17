from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin already exists
        if User.query.filter_by(username="admin_abrha").first():
            print("Admin already exists.")
            return

        admin = User(
            username="admin_abrha",
            password_hash=generate_password_hash("admin_secret_2026"),
            full_name="System Administrator",
            role="Admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("First Admin created successfully!")

if __name__ == '__main__':
    create_admin()