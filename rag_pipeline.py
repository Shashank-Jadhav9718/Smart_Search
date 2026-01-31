import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_ollama import OllamaLLM 
from langchain_core.documents import Document
from pdf2image import convert_from_path
import pytesseract

# ======================================================
# 1. ROBUST LOADING (OCR Support)
# ======================================================
def load_documents_with_ocr(file_path: str):
    print(f"\n--- 📂 Loading: {os.path.basename(file_path)} ---")
    try:
        # 1. Try standard digital load
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        valid_docs = [d for d in docs if len(d.page_content.strip()) > 20]
        if valid_docs: return valid_docs
    except Exception: pass

    # 2. Fallback to OCR
    print("⚠️ Digital load failed. Switching to OCR...")
    try:
        images = convert_from_path(file_path)
        ocr_docs = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            if len(text.strip()) > 20: 
                ocr_docs.append(Document(page_content=text, metadata={"source": file_path, "page": i}))
        return ocr_docs
    except Exception as e:
        print(f"❌ OCR Failed: {e}")
        return []

# ======================================================
# 2. CHUNKING (Optimized for Tables/Sections)
# ======================================================
def get_text_chunks(docs):
    # Large chunk size to keep tables and long sections intact
    splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=500)
    return splitter.split_documents(docs)

# ======================================================
# 3. VECTOR STORE
# ======================================================
def create_vector_store(chunks, user_id):
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    path = f"data/user_{user_id}/faiss_index"
    os.makedirs(path, exist_ok=True)
    vs = FAISS.from_documents(chunks, embeddings)
    vs.save_local(path)
    return vs

def load_vector_store(user_id):
    path = f"data/user_{user_id}/faiss_index"
    if not os.path.exists(os.path.join(path, "index.faiss")): return None
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2", model_kwargs={"device": "cpu"})
    return FAISS.load_local(path, embeddings, allow_dangerous_deserialization=True)


def build_rag_pipeline(user_id: int):
    vs = load_vector_store(user_id)
    if vs is None: raise ValueError("Index not found.")
    
    
    llm = OllamaLLM(model="mistral", temperature=0.1) 

    template = """
    You are a PROFESSIONAL DATA ANALYST.
    Answer the question based STRICTLY on the provided Context.

    INSTRUCTIONS:
    1. **Text & Sections:** If asked for a summary, conclusion, or specific section, extract the full text paragraphs.
    2. **Numbers & Data:** If asked for specific metrics (e.g., Revenue, Grades), extract the exact value.
    3. **Tables:** If the answer lies in a table, present it as a clean Markdown Table.
    4. **Formatting:** Use bullet points for lists. Bold key terms *only* if necessary for clarity.
    5. **Honesty:** If the information is not in the context, say "DATA_NOT_FOUND". Do not make up answers.

    Context:
    {context}

    Question: {question}

    Professional Answer:
    """
    
    prompt = PromptTemplate(template=template, input_variables=["context", "question"])
    
    
    retriever = vs.as_retriever(search_kwargs={"k": 12})

    def run(q: str):
        
        docs = retriever.invoke(q)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        
        
        response = llm.invoke(prompt.format(context=context_text, question=q))
        
        return response

    return run