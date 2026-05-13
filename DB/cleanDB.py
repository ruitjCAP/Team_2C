import chromadb

def reset_chroma_db(path="./chroma_db", confirm=True):
    client = chromadb.PersistentClient(path=path)

    collections = client.list_collections()

    if not collections:
        print("✅ No collections found. Database already clean.")
        return

    print("⚠️ Found collections:")
    for col in collections:
        print(f" - {col.name}")

    if confirm:
        user_input = input("\nAre you sure you want to delete ALL collections? (yes/no): ")
        if user_input.lower() != "yes":
            print("❌ Cancelled.")
            return

    for col in collections:
        client.delete_collection(name=col.name)
        print(f"🗑️ Deleted: {col.name}")

    print("✅ All collections deleted successfully!")

if __name__ == "__main__":
    reset_chroma_db()