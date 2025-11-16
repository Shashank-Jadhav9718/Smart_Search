import streamlit as st
import auth # Our auth logic
from database import SessionLocal, Logs, Documents, Users # Import DB models
import admin # The admin page
import datetime
import json
import os

# --- Imports for RAG pipeline ---
import rag_pipeline 
from database import SessionLocal

# --- FUNCTION TO LOAD CSS (We will disable the call to it) ---
def load_css(file_name):
    """Loads a local CSS file."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.error(f"CSS file '{file_name}' not found. Please create it.")

# --- Page Configuration ---
st.set_page_config(
    page_title="Smart Search",
    page_icon="🤖", # Reverted to original icon
    layout="wide"
)

# --- LOAD YOUR CUSTOM CSS (DISABLED) ---
# load_css("style.css")

# --- Session State Initialization ---
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = ""
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'role' not in st.session_state:
    st.session_state.role = ""
# --- Session State for Chat ---
if 'conversation_chain' not in st.session_state:
    st.session_state.conversation_chain = None
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'vector_store_loaded' not in st.session_state:
    st.session_state.vector_store_loaded = False

# --- Helper Function for Logging ---
def log_action(user_id, action, details=""):
    """Adds a log entry to the database."""
    db = SessionLocal()
    try:
        log_entry = Logs(
            user_id=user_id,
            action=action,
            details=json.dumps(details)
        )
        db.add(log_entry)
        db.commit()
    except Exception as e:
        print(f"Error logging action: {e}")
        db.rollback()
    finally:
        db.close()

# --- Login/Register UI ---
def show_login_page():
    """Displays the login and registration forms."""
    st.title("Welcome to 🤖 Smart Search")
    st.caption("Your AI-powered document Q&A system")

    choice = st.radio("Choose action:", ["Login", "Register"], horizontal=True)

    if choice == "Login":
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                user = auth.db_get_user(username)
                if user and auth.verify_password(password, user.hashed_password):
                    st.session_state.authenticated = True
                    st.session_state.username = user.username
                    st.session_state.user_id = user.id
                    st.session_state.role = user.role
                    
                    log_action(user.id, "LOGIN", f"User '{username}' logged in.")
                    
                    st.success(f"Logged in as {user.username}")
                    st.rerun() 
                else:
                    st.error("Invalid username or password")

    elif choice == "Register":
        st.subheader("Register New Account")
        with st.form("register_form"):
            new_username = st.text_input("Username", key="reg_username")
            new_password = st.text_input("Password", type="password", key="reg_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="reg_confirm_password")
            
            role_options = ["user", "admin"]
            new_role = st.selectbox("Select Role", role_options, index=0)
            submitted = st.form_submit_button("Register")

            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                elif not new_username or not new_password:
                    st.error("Please fill in all fields")
                else:
                    if auth.db_create_user(new_username, new_password, new_role):
                        st.success("Account created successfully! Please login.")
                        
                        admin_user = auth.db_get_user("admin")
                        log_action(admin_user.id if admin_user else 1, "REGISTER", f"New user '{new_username}' created with role '{new_role}'.")
                    else:
                        st.error("Username already exists")

# --- User Q&A Interface Function ---
def show_user_app():
    """Displays the main Q&A interface for 'user' role."""
    
    user_id = st.session_state.user_id
    
    # --- 1. Sidebar for File Upload ---
    with st.sidebar:
        st.header("Your Documents")
        uploaded_files = st.file_uploader(
            "Upload your PDFs here and click 'Process'", 
            type=["pdf"], 
            accept_multiple_files=True
        )
        
        if st.button("Process Documents"):
            if uploaded_files:
                
                # --- THIS IS THE FIX ---
                # We MUST reset the state *before* processing.
                # This releases the lock on the old faiss_index file
                # so that shutil.rmtree() can delete it.
                st.session_state.conversation_chain = None
                st.session_state.chat_history = []
                st.session_state.vector_store_loaded = False
                # -------------------------

                with st.spinner("Processing documents... This may take a moment."):
                    user_data_dir = f"data/user_{user_id}"
                    os.makedirs(user_data_dir, exist_ok=True)
                    
                    all_chunks = []
                    db = SessionLocal()
                    
                    for uploaded_file in uploaded_files:
                        file_path = os.path.join(user_data_dir, uploaded_file.name)
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # --- USE THE NEW OCR FUNCTION ---
                        docs = rag_pipeline.load_documents_with_ocr(file_path)
                        chunks = rag_pipeline.get_text_chunks(docs)
                        all_chunks.extend(chunks)
                        
                        new_doc = Documents(
                            user_id=user_id,
                            filename=uploaded_file.name,
                            file_path=file_path,
                            chunk_count=len(chunks)
                        )
                        db.add(new_doc)
                    
                    if all_chunks:
                        # This call will now succeed because the lock is gone
                        _, chunk_count = rag_pipeline.get_vector_store(all_chunks, user_id)
                        db.commit()
                        log_action(user_id, "UPLOAD", f"Processed {len(uploaded_files)} files. Total chunks: {chunk_count}")
                        st.success(f"Processed {len(uploaded_files)} documents!")
                        # No need to reset state here, we did it at the top
                    else:
                        st.warning("No text could be extracted from the documents.")
                    
                    db.close()
            else:
                st.warning("Please upload at least one PDF file.")

    # --- 2. Main Chat Interface ---
    st.title("🤖 Smart Search")
    st.caption("Ask questions about your uploaded documents.")

    # This code now runs *after* the state has been reset
    if not st.session_state.vector_store_loaded:
        vector_store = rag_pipeline.load_vector_store(user_id)
        if vector_store:
            # Re-create the chain with the new vector store
            st.session_state.conversation_chain = rag_pipeline.get_qa_chain(vector_store)
            st.session_state.vector_store_loaded = True
            st.info("Your documents are loaded and ready. Ask a question!")
        else:
            st.info("Please upload your PDF documents using the sidebar.")

    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input("What would you like to know?"):
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if st.session_state.conversation_chain:
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = st.session_state.conversation_chain({"query": prompt})
                        answer = response['result']
                        st.markdown(answer)
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                        
                        log_details = {"query": prompt, "answer": answer}
                        log_action(user_id, "QUERY", log_details)
                    except Exception as e:
                        # Catch API errors (or Ollama errors)
                        st.error(f"An error occurred while getting the answer: {e}")
                        log_action(user_id, "ERROR", f"LLM Error: {e}")
                        
        else:
            st.warning("Please upload and process your documents before asking questions.")

# --- Main Application Logic ---
def show_main_app():
    """
    This is the main application interface.
    It shows a logout button and routes to the correct panel.
    """
    st.sidebar.title(f"Welcome, {st.session_state.username}")
    st.sidebar.caption(f"Role: {st.session_state.role}")
    
    if st.sidebar.button("Logout"):
        log_action(st.session_state.user_id, "LOGOUT", f"User '{st.session_state.username}' logged out.")
        
        for key in st.session_state.keys():
            del st.session_state[key]
        
        st.rerun()

    if st.session_state.role == "admin":
        st.title("Admin Dashboard")
        admin.show_admin_dashboard()
    
    elif st.session_state.role == "user":
        show_user_app()
    
# --- App Entry Point ---
if not st.session_state.authenticated:
    show_login_page()
else:
    show_main_app()
