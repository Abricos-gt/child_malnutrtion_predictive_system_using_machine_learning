from app import app, db, User
from werkzeug.security import generate_password_hash

def create_admin():
    with app.app_context():
        # Check if admin already exists
        if User.query.filter_by(username="admin_abrha").first():
            print("Admin already exists.")
            return

        # Create admin with updated fields
        admin = User(
            username="admin_abrha",
            email="admin@malnutrition.org",  # Added email field
            password_hash=generate_password_hash("admin_secret_2026", method='pbkdf2:sha256'),
            role="Admin",
            is_verified=True # Ensures the admin can bypass verification checks
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("--- SUCCESS ---")
            print("First Admin 'admin_abrha' created successfully!")
            print("Password is: admin_secret_2026")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin: {e}")

if __name__ == '__main__':
    create_admin()