# 🔍 Smart Search: AI-Powered Multi-User Document Q&A System

## 🌟 Project Overview

**Smart Search** is a final-year computer science capstone project that transforms a basic PDF Q&A script into a secure, full-featured, and persistent web application. It utilizes **Retrieval-Augmented Generation (RAG)** to provide fast, accurate answers from uploaded documents, featuring robust multi-user management and administrative oversight.

**Final Status:** Fully functional, secure prototype ready for testing and deployment.

---

## ✨ Key Features

The system is designed with security and persistence in mind, offering distinct functionality for two user roles:

### 👤 Multi-User & Security
* **Role-Based Access Control (RBAC):** Secure login for **User** (Q&A access) and **Admin** (management access).
* **Persistent Storage:** All users, documents, and logs are stored permanently in a central **SQLite** database (`users.db`).
* **User Isolation:** Documents and vector indices (**FAISS**) are stored in dedicated, per-user file directories (`data/user_{id}/`).

### 🤖 RAG & Document Processing
* **Advanced Q&A:** Uses **OpenAI GPT-3.5** (via API) for highly accurate answer generation.
* **OCR Integration:** Features Optical Character Recognition (**Tesseract OCR**) fallback to successfully extract text and answer questions from **scanned or image-based PDFs**.
* **Cost-Effective Embeddings:** Utilizes the **free, local** Hugging Face embedding model (`all-MiniLM-L6-v2`) for cost-efficient vectorization.

### 📊 Admin Dashboard
* **User Management:** Admins can view, create, and securely delete user accounts (with automatic cleanup of user files).
* **Audit Logging:** Tracks all critical user actions (`LOGIN`, `UPLOAD`, `QUERY`) for a full audit trail.
* **Document Management:** Centralized view of all user-uploaded documents with file cleanup functionality.
* **System Analytics:** Metrics and visualizations of overall system activity.

---

## 🏗️ Architecture & Technology Stack

The project uses a standard multi-tier architecture implemented with Python and Streamlit.

### Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend/UI** | Streamlit, Custom CSS | Interactive web application and dark/purple theme. |
| **Backend** | Python, LangChain | Application routing, RAG pipeline orchestration. |
| **Database** | SQLite, SQLAlchemy | Persistent storage for users, documents, and logs. |
| **Vector Store** | FAISS, HuggingFaceEmbeddings | Efficient indexing and retrieval of document chunks. |
| **OCR** | Tesseract, PyTesseract | Text extraction from image-based PDFs. |

### Database Schema (`SmartSearchDB`)

The system is built on three linked tables:

* **Users** `(id, username, hashed_password, role)`
    * (1) -> (M) relationship with `Documents` and `Logs`.
* **Documents** `(id, user_id [FK], filename, file_path, chunk_count)`
* **Logs** `(id, user_id [FK], timestamp, action, details)`

---

## 🚀 Setup & Installation

Follow these steps to set up the environment and run the application locally.

### Prerequisites

1.  **Python 3.9+** installed.
2.  **OpenAI API Key** (required for the LLM).
3.  **Tesseract OCR:** Must be installed as a system executable.
    * **Windows:** Download the installer from the [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
    * **Linux/Mac:** Install via package manager (`sudo apt install tesseract-ocr` or `brew install tesseract`).
    * ***Note:** The default installation path for Tesseract on Windows (`C:\Program Files\Tesseract-OCR\`) is hardcoded in `rag_pipeline.py`.*

### Step-by-Step Guide

1.  **Clone the Repository** (or create the folder structure):
    ```bash
    mkdir smart-search-project
    cd smart-search-project
    mkdir data  # Empty folder for user data
    touch .env  # File for API keys
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  **Populate `requirements.txt`:**
    Create a file named `requirements.txt` and paste the following dependencies into it:
    ```
    streamlit
    streamlit-authenticator
    sqlalchemy
    bcrypt
    pypdf
    langchain
    langchain-community
    langchain-openai
    langchain_core
    langchain_text_splitters
    langchain_classic
    faiss-cpu
    python-dotenv
    plotly
    pdf2image
    pytesseract
    sentence-transformers
    ```

4.  **Install Libraries:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure API Key:**
    Open the `.env` file and add your OpenAI API key:
    ```env
    OPENAI_API_KEY=sk-...your-secret-key-here
    ```

6.  **Initialize Database & Admin User:**
    Run the `auth.py` script once to create the database file (`users.db`) and the default admin user:
    ```bash
    python auth.py
    ```

7.  **Run the Application:**
    ```bash
    streamlit run app.py
    ```

---

## 🔑 Usage and Credentials

### Default Credentials
| Role | Username | Password | Notes |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin` | `admin` | Used for system testing and management. |

### Testing OCR
To test the OCR functionality, log in as a regular user, upload a PDF that is known to be a **scanned image** (like a screenshot saved as a PDF), and click "Process Documents." You will see the OCR process activate in the terminal before the vector store is created.
