from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import os

# 1. SETUP: Point to the specific user's folder you want to inspect
USER_ID = 1 
folder_path = f"data/user_{USER_ID}/faiss_index"

# 2. CHECK: Does the folder exist?
if not os.path.exists(folder_path):
    print(f"❌ Error: No database found at {folder_path}")
    print("   (Did you process a document for this user yet?)")
    exit()

print(f"--- 📂 Inspecting Database at: {folder_path} ---")

# 3. LOAD: Open the database using the same embedding model
try:
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vs = FAISS.load_local(folder_path, embeddings, allow_dangerous_deserialization=True)
    
    # 4. STATS: How much data is here?
    print(f"✅ Database Loaded Successfully!")
    print(f"📊 Total Text Chunks Stored: {vs.index.ntotal}")
    
    # 5. PEEK: Show me the first few stored items
    print("\n--- 📝 SAMPLE CONTENT (First 3 Chunks) ---")
    
    # Access the internal dictionary of documents
    docstore = vs.docstore._dict
    
    count = 0
    for key, doc in docstore.items():
        print(f"\n[Chunk ID: {key}]")
        print(f"Source: {doc.metadata.get('source', 'Unknown')}")
        print(f"Page: {doc.metadata.get('page', 'Unknown')}")
        
        # FIX: Clean the text into a variable first to avoid the backslash error
        raw_text = doc.page_content[:200]
        clean_text = raw_text.replace('\n', ' ')
        
        print(f"Content Preview: {clean_text}...")
        
        count += 1
        if count >= 3: break 

except Exception as e:
    print(f"❌ Error reading database: {e}")