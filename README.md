# 🔍 Smart Search: AI-Powered Multi-User Document Q&A System

## 🌟 Project Overview

**Smart Search** is a final-year computer science capstone project that transforms a basic PDF Q&A script into a secure, full-featured, and persistent web application. It utilizes **Retrieval-Augmented Generation (RAG)** to provide fast, accurate, and **100% private** answers from uploaded documents, featuring robust multi-user management and administrative oversight.

This version runs entirely locally using **Ollama**, meaning **no API keys are required** and no data ever leaves your machine.

**Final Status:** Fully functional, secure prototype ready for testing and deployment.

---

## ✨ Key Features

The system is designed with security and persistence in mind, offering distinct functionality for two user roles:

### 👤 Multi-User & Security
* **Role-Based Access Control (RBAC):** Secure login for **User** (Q&A access) and **Admin** (management access).
* **Persistent Storage:** All users, documents, and logs are stored permanently in a central **SQLite** database (`users.db`).
* **User Isolation:** Documents and vector indices (**FAISS**) are stored in dedicated, per-user file directories (`data/user_{id}/`).

### 🤖 RAG & Document Processing
* **Local & Private Q&A:** Uses a **Local LLM (Ollama)** for private, offline, and no-cost answer generation (e.g., `mistral`).
* **OCR Integration:** Features Optical Character Recognition (**Tesseract OCR**) fallback to successfully extract text and answer questions from **scanned or image-based PDFs**.
* **Cost-Effective Embeddings:** Utilizes the **free, local** Hugging Face embedding model (`all-MiniLM-L6-v2`) for cost-efficient vectorization.

### 📊 Admin Dashboard
* **User Management:** Admins can view, create, and securely delete user accounts (with automatic cleanup of user files).
* **Audit Logging:** Tracks all critical user actions (`LOGIN`, `UPLOAD`, `QUERY`, `ERROR`) for a full audit trail.
* **Document Management:** Centralized view of all user-uploaded documents with file cleanup functionality.
* **System Analytics:** Metrics and visualizations (via Plotly) of overall system activity.

---

## 🏗️ Architecture & Technology Stack

The project uses a standard multi-tier architecture implemented with Python and Streamlit.

### Stack
| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend/UI** | Streamlit | Interactive web application. |
| **Backend** | Python, LangChain | Application routing, RAG pipeline orchestration. |
| **LLM (Local)** | **Ollama (Mistral)** | Local, private, no-cost answer generation. |
| **Database** | SQLite, SQLAlchemy | Persistent storage for users, documents, and logs. |
| **Vector Store** | FAISS, HuggingFaceEmbeddings | Efficient indexing and retrieval of document chunks. |
| **OCR** | Tesseract, PyTesseract | Text extraction from image-based PDFs. |
| **PDF Conversion** | Poppler, pdf2image | Converts PDF pages to images for OCR. |

### Database Schema (`SmartSearchDB`)
* **Users** `(id, username, hashed_password, role)`
    * (1) -> (M) relationship with `Documents` and `Logs`.
* **Documents** `(id, user_id [FK], filename, file_path, chunk_count)`
* **Logs** `(id, user_id [FK], timestamp, action, details)`

---

## 🚀 Setup & Installation

Follow these steps to set up the environment and run the application locally.

### Prerequisites (Crucial)

This project relies on three external "engines" that must be installed on your system and added to your **System PATH**.

1.  **Ollama:**
    * Download and install the [Ollama application](https://ollama.com/).
2.  **Tesseract OCR (The "Eyes"):**
    * Download the installer from the [UB-Mannheim Tesseract Wiki](https://github.com/UB-Mannheim/tesseract/wiki).
    * **Add to System PATH:** The installer usually does this, but confirm that `C:\Program Files\Tesseract-OCR` is in your System Environment `Path`.
3.  **Poppler (The "PDF-to-Image Converter"):**
    * Download the latest `.zip` release from [Poppler for Windows](https://github.com/oschwartz10612/poppler-windows/releases/).
    * Create a folder `C:\poppler` and extract the zip's contents into it.
    * **Add to System PATH:** Manually add the `bin` folder to your System `Path`: `C:\poppler\poppler-24.02.0-0\Library\bin` (or your version).

**Verify Installation:** After installing all three and restarting your terminal, these commands should work:
```bash
ollama --version
where tesseract
pdfinfo -v
