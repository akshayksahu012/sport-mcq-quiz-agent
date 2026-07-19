import os
import json
import chromadb
from chromadb.utils import embedding_functions

def get_chroma_client():
    """Initializes and returns a persistent ChromaDB client saving to disk."""
    return chromadb.PersistentClient(path="./chroma_db")

def setup_and_populate_db(json_file_path="./data/sports_facts.json"):
    """
    Reads the offline JSON facts, creates a collection, and populates it.
    This only needs to be run once, or when your local data changes.
    """
    client = get_chroma_client()

    # Using ChromaDB's default embedding function (sentence-transformers)
    # Alternatively, you can use OpenAI's embedding API
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()

    # Get or create collection
    collection = client.get_or_create_collection(
        name="sports_history",
        embedding_function=embedding_fn
    )

    # Check if the database has already been populated
    if collection.count() > 0:
        print(f"Database already populated with {collection.count()} facts.")
        return collection

    # Check if data file exists
    if not os.path.exists(json_file_path):
        print(f"Error: Raw fact data file not found at {json_file_path}")
        return collection

    # Load and parse facts
    with open(json_file_path, "r") as f:
        facts_list = json.load(f)

    documents = []
    metadata_list = []
    ids = []

    for idx, item in enumerate(facts_list):
        documents.append(item["fact"])
        # Storing metadata allows us to filter queries by sport later!
        metadata_list.append({"sport": item["sport"]})
        ids.append(f"fact_{idx}")

    # Bulk add vectors to collection
    collection.add(
        documents=documents,
        metadatas=metadata_list,
        ids=ids
    )
    print(f"Successfully vectorized and stored {len(documents)} facts.")
    return collection

def query_historic_facts(sport, query_text, n_results=2):
    """
    Queries ChromaDB for historic documents relating to a sport.
    Filters database elements to match the selected sport category.
    """
    client = get_chroma_client()
    embedding_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name="sports_history",
        embedding_function=embedding_fn
    )

    # Query with metadata filtering so we only get facts for our target sport
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where={"sport": sport}
    )

    # Return matched documents list (or empty list if none found)
    return results.get("documents", [[]])[0]