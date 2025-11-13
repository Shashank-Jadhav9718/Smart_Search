import bcrypt
from database import engine, Users, SessionLocal # <-- IMPORT SessionLocal HERE
import datetime # Make sure datetime is imported

# --- Password Hashing ---

def get_hashed_password(password: str) -> str:
    """Returns a hashed version of the password."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Checks if the plain password matches the hashed password."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Database Functions ---

def db_create_user(username: str, password: str, role: str = "user"):
    """
    Creates a new user in the database.
    Returns True if successful, False if user already exists.
    """
    db = SessionLocal() # Use the imported SessionLocal
    try:
        # Check if user already exists
        existing_user = db.query(Users).filter(Users.username == username).first()
        if existing_user:
            return False # User already exists
        
        # Create new user
        hashed_password = get_hashed_password(password)
        new_user = Users(
            username=username, 
            hashed_password=hashed_password, 
            role=role
        )
        db.add(new_user)
        db.commit()
        return True # User created successfully
    except Exception as e:
        print(f"Error creating user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def db_get_user(username: str):
    """
    Retrieves a user object from the database by username.
    Returns the user object or None.
    """
    db = SessionLocal() # Use the imported SessionLocal
    try:
        user = db.query(Users).filter(Users.username == username).first()
        return user
    finally:
        db.close()

# --- Initial Admin User ---
def create_default_admin():
    """
    Creates a default admin user if one doesn't already exist.
    This is useful for first-time setup.
    """
    print("Checking for default admin...")
    db = SessionLocal() # Use the imported SessionLocal
    try:
        admin_user = db.query(Users).filter(Users.role == "admin").first()
        if not admin_user:
            print("No admin found. Creating default admin...")
            db_create_user(
                username="admin", 
                password="admin",
                role="admin"
            )
            print("Default admin 'admin' with password 'admin' created.")
        else:
            print("Admin user already exists.")
    finally:
        db.close()

if __name__ == "__main__":
    # When we run 'python auth.py', it will:
    # 1. Initialize the database tables (in case we forgot)
    from database import init_db
    init_db() 
    
    # 2. Create the default admin user
    create_default_admin()