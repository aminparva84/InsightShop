import os
from config import Config

# Initialize ChromaDB client
vector_client = None
collection = None
chromadb = None

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None
    Settings = None

def _get_vector_db_path():
    """Resolve vector DB path to absolute so it is stable regardless of cwd."""
    path = Config.VECTOR_DB_PATH
    if os.path.isabs(path):
        return path
    # Relative path: resolve against project root (parent of utils/)
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(_root, path)


def init_vector_db():
    """Initialize the vector database for AI agent."""
    global vector_client, collection

    if chromadb is None:
        print("Warning: chromadb not installed, vector search will be disabled")
        return False

    try:
        vector_path = _get_vector_db_path()
        if not os.path.exists(vector_path):
            os.makedirs(vector_path)

        # Initialize ChromaDB
        vector_client = chromadb.PersistentClient(
            path=vector_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get or create collection
        collection = vector_client.get_or_create_collection(
            name="insightshop_products",
            metadata={"hnsw:space": "cosine"}
        )
        
        print("Vector database initialized successfully!")
        return True
    except Exception as e:
        print(f"Error initializing vector database: {e}")
        return False

def _safe_utf8(s):
    """Coerce value to a UTF-8-safe string for Chroma and logging (avoids charmap errors)."""
    if s is None:
        return ""
    raw = str(s)
    try:
        return raw.encode("utf-8", errors="replace").decode("utf-8")
    except Exception:
        return raw.encode("ascii", errors="replace").decode("ascii")


def _product_to_document_and_metadata(product_id, product_data):
    """Build document text and metadata dict for one product (for add/upsert)."""
    name = _safe_utf8(product_data.get("name", ""))
    desc = _safe_utf8(product_data.get("description", ""))
    category = _safe_utf8(product_data.get("category", ""))
    color = _safe_utf8(product_data.get("color", ""))
    size = _safe_utf8(product_data.get("size", ""))
    price = product_data.get("price", 0)
    text = f"{name} {desc} Category: {category} Color: {color} Size: {size} Price: ${price}"
    meta = {
        "product_id": product_id,
        "name": name[:255],
        "category": category[:50],
        "color": (color or "")[:50],
        "price": str(price),
    }
    return text, meta


def add_product_to_vector_db(product_id, product_data):
    """Add or update a product in the vector database (upsert so duplicates are overwritten)."""
    global collection

    if not collection:
        init_vector_db()

    if not collection:
        return False

    try:
        text, meta = _product_to_document_and_metadata(product_id, product_data)
        doc_id = f"product_{product_id}"
        # Use upsert so re-adding (e.g. after fix or re-sync) does not raise duplicate ID
        collection.upsert(
            documents=[text],
            ids=[doc_id],
            metadatas=[meta]
        )
        return True
    except Exception as e:
        print(f"Error adding product to vector DB: {e}")
        import traceback
        traceback.print_exc()
        return False

def search_products_vector(query, n_results=10):
    """Search products using vector similarity."""
    global collection
    
    if chromadb is None:
        return []
    
    if not collection:
        init_vector_db()
    
    if collection:
        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Extract product IDs from results
            product_ids = []
            if results['ids'] and len(results['ids']) > 0:
                for product_id_str in results['ids'][0]:
                    if product_id_str.startswith('product_'):
                        product_id = int(product_id_str.replace('product_', ''))
                        product_ids.append(product_id)
            
            return product_ids
        except Exception as e:
            print(f"Error searching vector DB: {e}")
            return []
    return []

def update_product_in_vector_db(product_id, product_data):
    """Update a product in the vector database (upsert overwrites existing id)."""
    return add_product_to_vector_db(product_id, product_data)


def delete_product_from_vector_db(product_id):
    """Remove a product from the vector database (e.g. when deactivated or deleted)."""
    global collection

    if chromadb is None:
        return True  # Nothing to do

    if not collection:
        init_vector_db()

    if collection:
        try:
            collection.delete(ids=[f"product_{product_id}"])
            return True
        except Exception as e:
            print(f"Error deleting product from vector DB: {e}")
            return False
    return True  # No collection is ok for delete (idempotent)


def is_vector_db_available():
    """Return True if the vector DB is initialized and usable."""
    global collection
    if chromadb is None or not collection:
        return False
    try:
        collection.peek(limit=1)
        return True
    except Exception:
        return False


def sync_all_products_from_sql(app, batch_size=50):
    """
    Sync all active products from SQLite to ChromaDB so AI search is up to date.
    Call at startup or when you need to reconcile vector DB with SQL.
    """
    if chromadb is None:
        print("Vector DB not available (chromadb not installed), skipping sync.")
        return 0

    if not init_vector_db() or not collection:
        print("Vector DB init failed, skipping sync.")
        return 0

    with app.app_context():
        from models.product import Product
        products = Product.query.filter_by(is_active=True).order_by(Product.id).all()
        total = len(products)
        if total == 0:
            print("No active products to sync to vector DB.")
            return 0

        synced = 0
        for i in range(0, total, batch_size):
            batch = products[i : i + batch_size]
            ids = []
            documents = []
            metadatas = []
            for p in batch:
                text, meta = _product_to_document_and_metadata(p.id, p.to_dict())
                ids.append(f"product_{p.id}")
                documents.append(text)
                metadatas.append(meta)
            try:
                collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
                synced += len(batch)
            except Exception as e:
                print(f"Error syncing batch to vector DB: {e}")
                for p in batch:
                    try:
                        add_product_to_vector_db(p.id, p.to_dict())
                        synced += 1
                    except Exception as e2:
                        print(f"Error syncing product {p.id} to vector DB: {e2}")

        print(f"Vector DB sync: {synced}/{total} active products indexed.")
        return synced

