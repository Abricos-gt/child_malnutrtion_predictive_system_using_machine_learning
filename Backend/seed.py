from app import app, db, User
from werkzeug.security import generate_password_hash

def update_admin():
    with app.app_context():
        # 1. Try to find the existing admin user by role
        admin = User.query.filter_by(role="Admin").first()

        if admin:
            print(f"Found existing admin '{admin.username}'. Updating credentials...")
            admin.username = "admin"
            admin.password_hash = generate_password_hash("09900990", method='pbkdf2:sha256')
            admin.is_verified = True
        else:
            print("No admin found. Creating a fresh one...")
            admin = User(
                username="admin",
                email="admin@malnutrition.org",
                password_hash=generate_password_hash("09900990", method='pbkdf2:sha256'),
                role="Admin",
                is_verified=True
            )
            db.session.add(admin)
        
        try:
            db.session.commit()
            print("--- SUCCESS ---")
            print("Username updated to: admin")
            print("Password updated to: 09900990")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating admin: {e}")

if __name__ == '__main__':
    update_admin()