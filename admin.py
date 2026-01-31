import streamlit as st
import pandas as pd
import plotly.express as px
from database import SessionLocal, Users, Documents, Logs # Import specific models
from auth import create_user # UPDATED IMPORT
import os
import shutil

# --- Database Session ---
def get_db():
    """Utility to get a new database session."""
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        print(f"Error getting DB session: {e}")
        db.close()
        return None

# --- Tab 1: User Management ---
def user_management():
    st.subheader("User Management")
    
    db = get_db()
    if not db:
        st.error("Could not connect to the database.")
        return

    # --- Add New User (in an expander) ---
    with st.expander("Add New User"):
        with st.form("add_user_form", clear_on_submit=True):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email (Optional)") # Added Email field
            new_password = st.text_input("Password", type="password")
            new_role = st.selectbox("Role", ["user", "admin"])
            submitted = st.form_submit_button("Create User")
            
            if submitted:
                if not new_username or not new_password:
                    st.warning("Please fill in all fields.")
                else:
                    # UPDATED FUNCTION CALL
                    # Matches the signature in auth.py: create_user(username, email, password, role)
                    success = create_user(new_username, new_email, new_password, new_role)
                    if success:
                        st.success(f"User '{new_username}' created successfully!")
                    else:
                        st.error(f"Username '{new_username}' already exists.")

    # --- List and Delete Users ---
    st.markdown("---")
    st.subheader("Existing Users")
    
    try:
        users = db.query(Users).all()
        user_data = [{
            "id": user.id, 
            "username": user.username, 
            "email": user.email,
            "role": user.role, 
            "created_at": user.created_at
        } for user in users]
        
        user_df = pd.DataFrame(user_data)
        
        # Display users in a dataframe
        st.dataframe(user_df, use_container_width=True)
        
        # --- Delete User ---
        st.markdown("---")
        st.subheader("Delete User")
        user_to_delete = st.selectbox("Select user to delete", [user.username for user in users if user.username != "admin"])
        
        if st.button(f"Delete User '{user_to_delete}'", type="primary"):
            if user_to_delete == "admin":
                st.error("Cannot delete the default admin account.")
            else:
                user_obj = db.query(Users).filter(Users.username == user_to_delete).first()
                if user_obj:
                    # Log before deleting
                    st.warning(f"Deleting user '{user_obj.username}' and all associated data...")
                    
                    # Delete associated files first
                    user_data_dir = f"data/user_{user_obj.id}"
                    if os.path.exists(user_data_dir):
                        try:
                            shutil.rmtree(user_data_dir)
                            st.success(f"Deleted file directory: {user_data_dir}")
                        except Exception as e:
                            st.error(f"Error deleting directory {user_data_dir}: {e}")

                    # Delete from DB (cascade will handle docs and logs)
                    db.delete(user_obj)
                    db.commit()
                    st.success(f"Successfully deleted user '{user_to_delete}'.")
                    st.rerun() # Rerun to update the lists
                else:
                    st.error("User not found.")
    except Exception as e:
        st.error(f"Error loading users: {e}")
    finally:
        db.close()

# --- Tab 2: Document Management ---
def document_management():
    st.subheader("All Uploaded Documents")
    
    db = get_db()
    if not db:
        st.error("Could not connect to the database.")
        return

    try:
        # Join Documents with Users to get username
        docs = db.query(Documents, Users.username).join(Users, Documents.user_id == Users.id).all()
        
        if not docs:
            st.info("No documents have been uploaded by any user yet.")
            return

        doc_data = [{
            "id": doc.Documents.id,
            "username": doc.username,
            "filename": doc.Documents.filename,
            "file_path": doc.Documents.file_path,
            "upload_date": doc.Documents.upload_date,
            "chunk_count": doc.Documents.chunk_count
        } for doc in docs]
        
        doc_df = pd.DataFrame(doc_data)
        st.dataframe(doc_df, use_container_width=True)

        # --- Delete Document ---
        st.markdown("---")
        st.subheader("Delete Document")
        doc_ids = doc_df['id']
        doc_to_delete_id = st.selectbox("Select document ID to delete", doc_ids)
        
        if st.button(f"Delete Document {doc_to_delete_id}", type="primary"):
            doc_obj = db.query(Documents).filter(Documents.id == doc_to_delete_id).first()
            if doc_obj:
                # 1. Delete the physical file
                try:
                    if os.path.exists(doc_obj.file_path):
                        os.remove(doc_obj.file_path)
                        st.success(f"Deleted file: {doc_obj.file_path}")
                    else:
                        st.warning("File not found, but deleting DB record.")
                    
                    # 2. Delete the DB record
                    db.delete(doc_obj)
                    db.commit()
                    st.success(f"Successfully deleted document record (ID: {doc_to_delete_id}).")
                    st.rerun() # Rerun to update list
                except Exception as e:
                    st.error(f"Error deleting file or DB record: {e}")
                    db.rollback()
            else:
                st.error("Document not found.")
                
    except Exception as e:
        st.error(f"Error loading documents: {e}")
    finally:
        db.close()

# --- Tab 3: Audit Logs ---
def audit_logs():
    st.subheader("System Audit Logs")
    
    db = get_db()
    if not db:
        st.error("Could not connect to the database.")
        return
        
    try:
        # Join Logs with Users to get username
        logs = db.query(Logs, Users.username).join(Users, Logs.user_id == Users.id).order_by(Logs.timestamp.desc()).all()
        
        if not logs:
            st.info("No log entries found.")
            return

        log_data = [{
            "id": log.Logs.id,
            "username": log.username,
            "action": log.Logs.action,
            "details": log.Logs.details,
            "timestamp": log.Logs.timestamp
        } for log in logs]
        
        log_df = pd.DataFrame(log_data)
        st.dataframe(log_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading logs: {e}")
    finally:
        db.close()

# --- Tab 4: System Stats ---
def system_stats():
    st.subheader("System Statistics")
    
    db = get_db()
    if not db:
        st.error("Could not connect to the database.")
        return

    try:
        # --- Key Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Users", db.query(Users).count())
        col2.metric("Total Documents", db.query(Documents).count())
        col3.metric("Total Log Entries", db.query(Logs).count())
        
        st.markdown("---")

        # --- Chart: Uploads Over Time ---
        st.subheader("Document Uploads Over Time")
        docs = db.query(Documents).all()
        if docs:
            doc_df = pd.DataFrame([{"upload_date": doc.upload_date} for doc in docs])
            doc_df['upload_date'] = pd.to_datetime(doc_df['upload_date']).dt.date
            uploads_by_date = doc_df.groupby('upload_date').size().reset_index(name='count')
            
            fig = px.bar(uploads_by_date, x='upload_date', y='count', title="Uploads per Day")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No document data to display.")

        # --- Chart: Activity by User ---
        st.subheader("Logs by User")
        logs = db.query(Logs, Users.username).join(Users, Logs.user_id == Users.id).all()
        if logs:
            log_df = pd.DataFrame([{"username": log.username} for log in logs])
            logs_by_user = log_df.groupby('username').size().reset_index(name='count')
            
            fig2 = px.pie(logs_by_user, names='username', values='count', title="Log Entries by User")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No log data to display.")
            
    except Exception as e:
        st.error(f"Error generating stats: {e}")
    finally:
        db.close()

# --- Main Function to be called by app.py ---
def show_admin_dashboard():
    """Renders the admin dashboard with tabs."""
    
    tab_titles = [
        "User Management",
        "Document Management",
        "Audit Logs",
        "System Stats"
    ]
    tab1, tab2, tab3, tab4 = st.tabs(tab_titles)

    with tab1:
        user_management()

    with tab2:
        document_management()

    with tab3:
        audit_logs()

    with tab4:
        system_stats()