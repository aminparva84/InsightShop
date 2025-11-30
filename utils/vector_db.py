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

def init_vector_db():
    """Initialize the vector database for AI agent."""
    global vector_client, collection
    
    if chromadb is None:
        print("Warning: chromadb not installed, vector search will be disabled")
        return False
    
    try:
        # Create vector database directory if it doesn't exist
        if not os.path.exists(Config.VECTOR_DB_PATH):
            os.makedirs(Config.VECTOR_DB_PATH)
        
        # Initialize ChromaDB
        vector_client = chromadb.PersistentClient(
            path=Config.VECTOR_DB_PATH,
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

def add_product_to_vector_db(product_id, product_data):
    """Add a product to the vector database."""
    global collection
    
    if not collection:
        init_vector_db()
    
    if collection:
        try:
            # Create text representation for embedding
            text = f"{product_data.get('name', '')} {product_data.get('description', '')} Category: {product_data.get('category', '')} Color: {product_data.get('color', '')} Size: {product_data.get('size', '')} Price: ${product_data.get('price', 0)}"
            
            # Add to collection (ChromaDB will handle embedding)
            collection.add(
                documents=[text],
                ids=[f"product_{product_id}"],
                metadatas=[{
                    'product_id': product_id,
                    'name': product_data.get('name', ''),
                    'category': product_data.get('category', ''),
                    'color': product_data.get('color', ''),
                    'price': str(product_data.get('price', 0))
                }]
            )
            return True
        except Exception as e:
            print(f"Error adding product to vector DB: {e}")
            return False
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
    """Update a product in the vector database."""
    # Remove old entry and add new one
    global collection
    
    if not collection:
        init_vector_db()
    
    if collection:
        try:
            # Delete old entry
            try:
                collection.delete(ids=[f"product_{product_id}"])
            except:
                pass
            
            # Add updated entry
            return add_product_to_vector_db(product_id, product_data)
        except Exception as e:
            print(f"Error updating product in vector DB: {e}")
            return False
    return False

