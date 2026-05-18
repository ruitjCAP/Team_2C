import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
import os

# Load env vars
load_dotenv()

BASE_URL = os.getenv("base_url")

# Connect to DB
client = chromadb.PersistentClient(path="./chroma_db")

# Get collection (IMPORTANT: must pass same embedding function)
collection = client.get_collection(
    name="Compliance_files",
    embedding_function=OpenAIEmbeddingFunction(
        model_name="text-embedding-3-small",
        api_key =os.getenv("API_KEY"),
        api_base=BASE_URL
    )
)

# Your query
#query = input("❓ Ask a question: ")

# Run query
def rag(query):
    results = collection.query(
        query_texts=[query],
        n_results=5
    )

    # Print results nicely
    docs = results["documents"][0]
    metas = results.get("metadatas", [[]])[0]
    query_results = "\n🔎 Results:\n"

    
    

    for i, doc in enumerate(docs):
        query_results += f"--- Result {i+1} ---"
        if metas and i < len(metas):
            query_results += f"📄 Source: {metas[i].get('source')}"
        query_results+=doc[:500]  # limit output
        query_results+="\n"
    return query_results

# print(rag(query))


if __name__ == "__main__":
    query = input("❓ Ask a question: ")
    print(rag(query))