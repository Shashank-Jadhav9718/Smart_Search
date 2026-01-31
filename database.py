from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import bcrypt
import datetime
import json

# --- DATABASE SETUP ---
DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELS ---
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    role = Column(String, default="user")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Documents(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_count = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"))

class Logs(Base):
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))

# Create tables
Base.metadata.create_all(bind=engine)

# --- CORE FUNCTIONS ---
def create_user(username, email, password, role="user"):
    session = SessionLocal()
    try:
        if session.query(User).filter(User.username == username).first():
            return False
        
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        new_user = User(username=username, email=email, password_hash=hashed_pw, role=role)
        session.add(new_user)
        session.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        session.rollback()
        return False
    finally:
        session.close()

def authenticate_user(username, password):
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.username == username).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return user
        return None
    finally:
        session.close()

# Export specific models for other files
Users = User