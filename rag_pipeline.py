import os
import shutil
from dotenv import load_dotenv

# --- Imports for Embeddings ---
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# --- Imports for the LLM (Gemini) ---
from langchain_classic.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

# --- NEW IMPORTS FOR OCR ---
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
from langchain_core.documents import Document # Used to create documents from OCR text

# --- CONFIGURE TESSERACT INSTALLATION PATH ---
# Tell pytesseract where to find the .exe file you installed
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# --- Environment Setup ---

def load_api_key():
    """Loads the Google API key from the .env file."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in .env file. Please add it.")
    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key

# --- 1. Document Loading (UPGRADED WITH OCR) ---

def load_documents_with_ocr(file_path: str):
    """
    Loads a PDF, attempting to read digital text first.
    If it fails or finds no text, it falls back to OCR.
    """
    print(f"Loading document from {file_path}")
    
    # 1. Try standard digital text extraction
    try:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        # Check if text was actually extracted
        if docs and docs[0].page_content.strip():
            print("Successfully loaded digital text.")
            return docs
    except Exception as e:
        print(f"Standard PyPDF loading failed: {e}. Attempting OCR.")

    # 2. Fallback to OCR if digital text fails
    print("Falling back to OCR... (This may take a moment)")
    try:
        # Convert PDF pages to images
        images = convert_from_path(file_path)
        all_text = ""
        
        # Process each image with Tesseract
        for i, img in enumerate(images):
            print(f"Processing page {i+1}/{len(images)} with OCR...")
            text = pytesseract.image_to_string(img, lang='eng')
            all_text += text + "\n\n--- PAGE BREAK ---\n\n"
            
        if not all_text.strip():
            print("OCR processing finished, but no text was found.")
            return []

        # Create a single LangChain 'Document' from all the OCR text
        ocr_doc = Document(
            page_content=all_text,
            metadata={"source": file_path, "ocr": True}
        )
        print("OCR processing successful.")
        return [ocr_doc] # Return as a list to match PyPDFLoader's output

    except Exception as ocr_error:
        print(f"Fatal error during OCR processing: {ocr_error}")
        return [] # Return empty list if everything fails

# --- 2. Text Chunking (No Change) ---

def get_text_chunks(docs):
    """Splits loaded documents into smaller chunks for processing."""
    print("Splitting text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(docs)
    print(f"Created {len(chunks)} chunks.")
    return chunks

# --- 3. Vector Store (No Change) ---

def get_vector_store(text_chunks, user_id: int):
    """Creates and saves a FAISS vector store from text chunks."""
    print("Creating vector store with Hugging Face embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'} 
    )
    user_data_dir = f"data/user_{user_id}"
    vector_store_path = os.path.join(user_data_dir, "faiss_index")
    if os.path.exists(vector_store_path):
        shutil.rmtree(vector_store_path)
    vector_store = FAISS.from_documents(documents=text_chunks, embedding=embeddings)
    vector_store.save_local(vector_store_path)
    print(f"Vector store saved to {vector_store_path}")
    return vector_store, len(text_chunks)

def load_vector_store(user_id: int):
    """Loads an existing FAISS vector store from a user's folder."""
    embeddings = HuggingFaceEmbeddings(
        model_name="all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    vector_store_path = os.path.join(f"data/user_{user_id}", "faiss_index")
    if not os.path.exists(vector_store_path):
        return None
    print(f"Loading vector store from {vector_store_path}")
    vector_store = FAISS.load_local(vector_store_path, embeddings, allow_dangerous_deserialization=True)
    return vector_store

# --- 4. Q&A Chain (Using Gemini) ---

PROMPT_TEMPLATE = """
You are a helpful AI assistant. Use the following context to answer the question.
If you don't know the answer, just say you don't know. Do not try to make up an answer.

Context:
{context}

Question:
{question}

Helpful Answer:
"""

def get_qa_chain(vector_store):
    """Creates a RetrievalQA chain using the Google Gemini model."""
    print("Creating Q&A chain with Google Gemini...")
    load_api_key()
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",  # Use the modern flash model
        temperature=0.7,
        convert_system_message_to_human=True
    )
    prompt = PromptTemplate(
        template=PROMPT_TEMPLATE, 
        input_variables=["context", "question"]
    )
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever(),
        chain_type_kwargs={"prompt": prompt},
        return_source_documents=True
    )
    print("Gemini Q&A chain created.")
    return qa_chain