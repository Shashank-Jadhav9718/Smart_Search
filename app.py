import streamlit as st
import auth 
from database import SessionLocal, Logs, Documents, Users 
import admin 
import datetime
import json
import os
import rag_pipeline 
import time

# 1. PAGE CONFIG
st.set_page_config(page_title="Smart Search", page_icon="🤖", layout="wide")

# 2. SESSION STATE
if 'authenticated' not in st.session_state:
    st.session_state.update({
        'authenticated': False, 
        'chat_history': [], 
        'vector_store_loaded': False, 
        'user_id': None, 
        'qa_pipeline': None,
        'username': "",
        'role': "",
        'processing_complete': False, 
        'last_uploaded_ids': []
    })

# 3. HELPER: LOGGING
def log_action(user_id, action, details=""):
    db = SessionLocal()
    try:
        log_entry = Logs(user_id=user_id, action=action, details=json.dumps(details))
        db.add(log_entry)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

# 4. LOGIN SCREEN
def show_login_page():
    st.title("🤖 Smart Search")
    
    tab1, tab2 = st.tabs(["Login", "Register"])

    # Login Tab
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            if st.form_submit_button("Login"):
                user = auth.authenticate_user(username, password)
                if user:
                    st.session_state.update({
                        'authenticated': True,
                        'user_id': user.id,
                        'username': user.username,
                        'role': user.role
                    })
                    log_action(user.id, "LOGIN", "User logged in")
                    st.rerun()
                else:
                    st.error("Invalid credentials")

    # Register Tab
    with tab2:
        with st.form("reg_form"):
            st.subheader("Create Account")
            new_user = st.text_input("New Username")
            new_email = st.text_input("Email")
            new_pass = st.text_input("New Password", type="password")
            new_role = st.selectbox("Select Role", ["user", "admin"]) 

            if st.form_submit_button("Register"):
                if auth.create_user(new_user, new_email, new_pass, role=new_role):
                    st.success(f"Account created as '{new_role}'! Please login.")
                else:
                    st.error("User already exists.")

# 5. USER INTERFACE
def show_user_app():
    user_id = st.session_state.user_id
    
    with st.sidebar:
        st.header("Upload Documents")
        files = st.file_uploader("Upload PDF", type=["pdf"], accept_multiple_files=True)
        
        # Check for new files to reset "Process" state
        current_file_ids = [f.name + str(f.size) for f in files] if files else []
        if st.session_state.last_uploaded_ids != current_file_ids:
            st.session_state.processing_complete = False
            st.session_state.last_uploaded_ids = current_file_ids

        if files:
            # Logic: Show Button ONLY if not processed yet
            if not st.session_state.processing_complete:
                if st.button("Process Documents"):
                    
                    # Initialize Progress Bar
                    progress_bar = st.progress(0, text="Starting engine...")
                    
                    # Reset State
                    st.session_state.qa_pipeline = None
                    st.session_state.chat_history = []
                    st.session_state.vector_store_loaded = False
                    
                    user_path = f"data/user_{user_id}"
                    os.makedirs(user_path, exist_ok=True)
                    all_chunks = []
                    total_files = len(files)
                    
                    # Processing Loop
                    for i, f in enumerate(files):
                        progress = int((i / total_files) * 80)
                        progress_bar.progress(progress, text=f"Scanning {f.name}...")
                        
                        path = os.path.join(user_path, f.name)
                        with open(path, "wb") as b: b.write(f.getbuffer())
                        
                        docs = rag_pipeline.load_documents_with_ocr(path)
                        all_chunks.extend(rag_pipeline.get_text_chunks(docs))
                        
                        db = SessionLocal()
                        if not db.query(Documents).filter_by(filename=f.name, user_id=user_id).first():
                            db.add(Documents(filename=f.name, file_path=path, user_id=user_id))
                            db.commit()
                        db.close()

                    if all_chunks:
                        progress_bar.progress(90, text="Building Index...")
                        rag_pipeline.create_vector_store(all_chunks, user_id)
                        
                        progress_bar.progress(100, text="Done!")
                        time.sleep(0.5)
                        
                        st.session_state.processing_complete = True
                        st.rerun()
                    else:
                        st.warning("No text found.")
            else:
                st.success("✅ System Ready")
        else:
            st.info("Waiting for files...")

    # --- MAIN CHAT AREA ---
    st.title("🤖 Smart Search")
    
    if st.session_state.processing_complete and not st.session_state.vector_store_loaded:
        try:
            st.session_state.qa_pipeline = rag_pipeline.build_rag_pipeline(user_id)
            st.session_state.vector_store_loaded = True
        except: pass

    # Display Chat History (Standard Streamlit)
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a question about your documents..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.rerun()

    # Generate Response
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                if st.session_state.qa_pipeline:
                    try:
                        answer = st.session_state.qa_pipeline(st.session_state.chat_history[-1]["content"])
                        st.write(answer)
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        log_action(user_id, "QUERY", {"q": st.session_state.chat_history[-2]["content"], "a": answer})
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.write("Please upload and process documents first.")
                    st.session_state.chat_history.append({"role": "assistant", "content": "Please upload and process documents first."})

# 6. ROUTING LOGIC
if not st.session_state.authenticated:
    show_login_page()
else:
    st.sidebar.markdown("---")
    st.sidebar.caption(f"User: {st.session_state.username}")
    
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()
        
    if st.session_state.role == "admin":
        admin.show_admin_dashboard()
    else:
        show_user_app()