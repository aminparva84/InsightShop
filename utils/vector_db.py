import os
from config import Config

# Initialize ChromaDB client
vector_client = None
collection = None
chromadb = None
chromadb_import_error = None  # Reason chromadb is unavailable (for diagnostics)

try:
    import chromadb
    from chromadb.config import Settings
except Exception as e:
    chromadb = None
    Settings = None
    chromadb_import_error = str(e)

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
    """Build document text and metadata dict for one product (for add/upsert). Include sale info so 'sale' queries match."""
    name = _safe_utf8(product_data.get("name", ""))
    desc = _safe_utf8(product_data.get("description", ""))
    category = _safe_utf8(product_data.get("category", ""))
    color = _safe_utf8(product_data.get("color", ""))
    size = _safe_utf8(product_data.get("size", ""))
    price = product_data.get("price", 0)
    display_brand = _safe_utf8(product_data.get("display_brand", "") or product_data.get("brand", ""))
    fabric = _safe_utf8(product_data.get("fabric", ""))
    clothing_type = _safe_utf8(product_data.get("clothing_type", ""))
    occasion = _safe_utf8(product_data.get("occasion", ""))
    on_sale = product_data.get("on_sale", False)
    discount = product_data.get("discount_percentage")
    sale_part = " On sale." if on_sale else ""
    if on_sale and discount is not None:
        sale_part = f" On sale. {discount}% off." + sale_part
    text = f"{name} {desc} Category: {category} Color: {color} Size: {size} Price: ${price} Brand: {display_brand} Fabric: {fabric} Type: {clothing_type} Occasion: {occasion}{sale_part}"
    meta = {
        "product_id": product_id,
        "name": name[:255],
        "category": category[:50],
        "color": (color or "")[:50],
        "price": str(price),
        "brand": (display_brand or "")[:100],
        "on_sale": "true" if on_sale else "false",
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


def get_chromadb_status():
    """Return (available: bool, message: str) for ChromaDB. Use for admin/API messages."""
    if chromadb is not None:
        return True, ""
    if chromadb_import_error:
        return False, chromadb_import_error
    return False, "ChromaDB not installed"


def sync_all_products_from_sql(app=None, batch_size=50):
    """
    Sync all active products from SQLite to ChromaDB so AI search is up to date.
    Call at startup with app, or from a request (no args) to use current app context.
    Returns (synced_count, chromadb_available). When ChromaDB is not installed or
    init fails, returns (0, False) so the app can keep working with keyword search.
    """
    if chromadb is None:
        msg = chromadb_import_error or "chromadb not installed"
        print(f"Vector DB not available ({msg}). AI search uses keyword/direct search.")
        return 0, False

    if not init_vector_db() or not collection:
        print("Vector DB init failed. AI search uses keyword/direct search.")
        return 0, False

    def _run_sync():
        from models.product import Product
        products = Product.query.filter_by(is_active=True).order_by(Product.id).all()
        total = len(products)
        if total == 0:
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

    try:
        if app is not None:
            with app.app_context():
                return _run_sync(), True
        from flask import current_app
        app = current_app._get_current_object()
        with app.app_context():
            return _run_sync(), True
    except Exception as e:
        print(f"Vector DB sync error: {e}")
        return 0, False

