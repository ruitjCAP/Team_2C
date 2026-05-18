import os
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
import pdfplumber
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from  cleanDB import reset_chroma_db 

def get_context(query, n_results=5):
    collection = get_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results
    )

    docs = results["documents"][0]
    context = "\n\n".join(docs)

    return context
def chunk_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap

    return chunks

def extract_text_from_pdf(path,ocr_language='eng'):
    text = ""

    with fitz.open(path) as pdf:
        for page_number in range(len(pdf)):
            page = pdf[page_number]
            pix = page.get_pixmap(dpi=300)
            image = Image.open(io.BytesIO(pix.tobytes("png")))
            page_text = pytesseract.image_to_string(image, lang=ocr_language)
            if page_text.strip():
                text += page_text + "\n"

    return text

load_dotenv()

BASE_URL = os.getenv("base_url")

def get_collection():
    client = chromadb.PersistentClient(path="./chroma_db")

    collection = client.get_or_create_collection(
        name="Compliance_files",
        embedding_function=OpenAIEmbeddingFunction(
            model_name="text-embedding-3-small",
            api_key_env_var="API_KEY",
            api_base=BASE_URL
        )
    )

    return collection

def ingest_pdfs(folder_path="./pdfs"):
    collection = get_collection()

    for file in os.listdir(folder_path):
        if file.endswith(".pdf") and file =="Policies_OCR.pdf":
            
            path = os.path.join(folder_path, file)

            print(f"Processing {file}...")

            text = extract_text_from_pdf(path)
            text = text.replace("\n", " ").strip()

            chunks = chunk_text(text)

            ids = [f"{file}_{i}" for i in range(len(chunks))]
            metadatas = [{"source": file, "chunk": i} for i in range(len(chunks))]

            
            batch_size = 5
            total = len(chunks)

            for i in range(0, total, batch_size):
                collection.add(
                    ids=ids[i:i+batch_size],
                    documents=chunks[i:i+batch_size],
                    metadatas=metadatas[i:i+batch_size]
                )

                print(f"✅ Processed {min(i + batch_size, total)} / {total} chunks")


    print("✅ Ingestion complete")


reset_chroma_db()

# STEP 1: Load PDFs (run once)
ingest_pdfs("./pdfs")

# STEP 2: Query
question = "What is this document about?"

context = get_context(question) 

print("\n--- CONTEXT ---\n")
print(context)