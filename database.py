import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.engine import Engine
import datetime

# --- Database Setup ---

# Define the database URL (we are using SQLite, which stores the DB in a file)
DATABASE_URL = "sqlite:///users.db"

# Create the SQLAlchemy engine
# 'check_same_thread=False' is needed for SQLite to work with Streamlit
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# ...
Base = declarative_base()

# Create a 'SessionLocal' class for creating database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Table Models ---


class Users(Base):
    """
    Users table model.
    Stores user credentials and role.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user", nullable=False) # 'user' or 'admin'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # --- Relationships ---
    # Defines the 'one-to-many' relationship with Documents and Logs
    # 'documents' will be a list of Document objects associated with this user
    documents = relationship("Documents", back_populates="owner", cascade="all, delete-orphan")
    logs = relationship("Logs", back_populates="user", cascade="all, delete-orphan")

class Documents(Base):
    """
    Documents table model.
    Stores metadata about uploaded files.
    """
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False) # Path to the file in 'data/user_{id}/'
    upload_date = Column(DateTime, default=datetime.datetime.utcnow)
    chunk_count = Column(Integer, default=0)

    # --- Relationships ---
    # Defines the 'many-to-one' relationship back to Users
    owner = relationship("Users", back_populates="documents")

class Logs(Base):
    """
    Logs table model.
    Acts as an audit trail for user actions.
    """
    __tablename__ = "logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Foreign key
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    action = Column(String, nullable=False) # e.g., "UPLOAD", "QUERY", "LOGIN"
    details = Column(JSON, nullable=True) # Store extra info like query text

    # --- Relationships ---
    user = relationship("Users", back_populates="logs")

# --- Database Initialization ---

def init_db():
    """
    Creates all the tables in the database based on the models defined.
    """
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")

# This makes the file runnable. If we run 'python database.py'
# in the terminal, it will call init_db()
if __name__ == "__main__":
    init_db()