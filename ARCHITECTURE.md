# InsightShop AI Architecture & Database Schema

## 🏗️ AI Architecture - Layer Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│                    (React Frontend - AIChat.js)                  │
│  • User Interface & Chat Interface                              │
│  • Voice Input/Output (Speech Recognition & Synthesis)          │
│  • Product Display & Selection                                  │
│  • Conversation History Management                               │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                                │
│                    (Flask Routes - ai_agent.py)                 │
│  • /api/ai/chat - Main conversational endpoint                  │
│  • /api/ai/search - Vector-based product search                  │
│  • /api/ai/filter - AI-powered filtering                        │
│  • /api/ai/compare - Product comparison                         │
│  • /api/ai/text-to-speech - AWS Polly integration               │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  PROCESSING  │    │   SEARCH     │    │  KNOWLEDGE    │
│    LAYER     │    │    LAYER     │    │     BASE      │
│              │    │              │    │               │
│ • Intent     │    │ • Vector     │    │ • Fashion     │
│   Detection  │    │   Search     │    │   Knowledge   │
│ • Entity     │    │   (ChromaDB) │    │ • Color       │
│   Extraction │    │ • SQL        │    │   Matching    │
│ • Context    │    │   Queries    │    │ • Fabric      │
│   Building   │    │ • Filtering  │    │   Info        │
│              │    │              │    │ • Occasions   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AI/ML LAYER                                 │
│                  (AWS Bedrock - Claude 3)                       │
│  • Large Language Model (Claude 3 Sonnet/Haiku)                 │
│  • Natural Language Understanding                               │
│  • Conversational AI                                            │
│  • Context-Aware Responses                                       │
│  • Fashion Expertise Integration                                 │
└────────────────────────────┬────────────────────────────────────┘
                              │
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   VECTOR     │    │  RELATIONAL  │    │   EXTERNAL   │
│  DATABASE    │    │   DATABASE   │    │   SERVICES    │
│              │    │              │    │               │
│ • ChromaDB   │    │ • SQLite     │    │ • AWS Bedrock │
│ • Embeddings │    │ • Products   │    │ • AWS Polly   │
│ • Semantic   │    │ • Users     │    │ • Boto3 SDK   │
│   Search     │    │ • Orders     │    │               │
│              │    │ • Cart       │    │               │
│              │    │ • Payments   │    │               │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 🔄 AI Request Flow

```
User Input
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ 1. INTENT DETECTION & ENTITY EXTRACTION                      │
│    • Detect category (men/women/kids)                       │
│    • Extract color, size, clothing type                      │
│    • Identify occasion, age group, dress style               │
│    • Check for comparison requests                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SEARCH STRATEGY SELECTION                                 │
│    IF (strict filters detected):                             │
│      → Direct SQL Query with filters                         │
│    ELSE:                                                     │
│      → Vector Search (ChromaDB)                              │
│      → Fallback to SQL if vector search fails               │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. CONTEXT BUILDING                                          │
│    • Get matching products from search                      │
│    • Load fashion knowledge base                             │
│    • Build system prompt with:                               │
│      - Product database context                              │
│      - Fashion knowledge (colors, fabrics, occasions)        │
│      - Styling advice                                        │
│    • Create user prompt with conversation history            │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. LLM PROCESSING (AWS Bedrock)                              │
│    • Send prompt to Claude 3                                 │
│    • Receive natural language response                       │
│    • Extract product IDs from response                       │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. RESPONSE FORMATTING                                       │
│    • Combine AI response with product data                  │
│    • Set action type (search_results, compare, etc.)       │
│    • Return to frontend with:                                │
│      - Text response                                         │
│      - Suggested products                                    │
│      - Product IDs                                           │
│      - Action type                                           │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
                    Frontend Display
```

## 🗄️ Database Schema

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                           USERS TABLE                                │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│     email                 VARCHAR(255) UNIQUE, INDEX                 │
│     password_hash         VARCHAR(255) NULLABLE                      │
│     first_name            VARCHAR(100)                               │
│     last_name             VARCHAR(100)                               │
│     is_verified           BOOLEAN DEFAULT FALSE                     │
│     verification_token    VARCHAR(255) NULLABLE                     │
│     verification_token_   DATETIME NULLABLE                          │
│       expires                                                         │
│     reset_token           VARCHAR(255) NULLABLE                     │
│     reset_token_expires   DATETIME NULLABLE                          │
│     google_id             VARCHAR(255) UNIQUE, INDEX, NULLABLE      │
│     facebook_id           VARCHAR(255) UNIQUE, INDEX, NULLABLE      │
│     profile_picture       VARCHAR(500) NULLABLE                      │
│     created_at            DATETIME                                   │
│     updated_at            DATETIME                                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             │ 1:N
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CART_ITEMS   │    │   ORDERS     │    │   (Future)    │
│              │    │              │    │   Reviews    │
└──────────────┘    └──────────────┘    └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        PRODUCTS TABLE                                 │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│     name                  VARCHAR(255) INDEX                         │
│     description           TEXT                                       │
│     price                 NUMERIC(10,2)                              │
│     category              VARCHAR(50) INDEX                           │
│                          (men, women, kids)                          │
│     color                 VARCHAR(50) INDEX                          │
│     size                  VARCHAR(20)                                 │
│     available_colors      TEXT (JSON array)                          │
│     available_sizes        TEXT (JSON array)                          │
│     fabric                VARCHAR(100) INDEX                         │
│     clothing_type         VARCHAR(100) INDEX                          │
│                          (T-Shirt, Dress, Jeans, etc.)              │
│     dress_style           VARCHAR(100) INDEX                          │
│                          (scoop, v-neck, bow, etc.)                  │
│     occasion              VARCHAR(100) INDEX                         │
│                          (wedding, business_formal, casual, etc.)   │
│     age_group             VARCHAR(50) INDEX                          │
│                          (young_adult, mature, senior, all)          │
│     image_url             VARCHAR(500)                               │
│     stock_quantity        INTEGER DEFAULT 0                          │
│     is_active             BOOLEAN DEFAULT TRUE, INDEX                │
│     rating                NUMERIC(3,2) DEFAULT 0.0                   │
│     review_count           INTEGER DEFAULT 0                          │
│     slug                  VARCHAR(255) UNIQUE, INDEX                │
│     meta_title            VARCHAR(255)                               │
│     meta_description      TEXT                                       │
│     created_at            DATETIME                                   │
│     updated_at            DATETIME                                   │
│                                                                       │
│ COMPOSITE INDEXES:                                                   │
│   • idx_category_occasion (category, occasion)                       │
│   • idx_category_age_group (category, age_group)                     │
│   • idx_category_clothing_type (category, clothing_type)            │
│   • idx_occasion_age_group (occasion, age_group)                     │
│   • idx_category_price (category, price)                            │
│   • idx_category_fabric (category, fabric)                           │
│   • idx_is_active_category (is_active, category)                    │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             │ 1:N
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ CART_ITEMS   │    │ ORDER_ITEMS │    │ VECTOR_DB    │
│              │    │              │    │ (ChromaDB)   │
└──────────────┘    └──────────────┘    └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        CART_ITEMS TABLE                              │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│ FK  user_id               INTEGER → users.id, INDEX                 │
│ FK  product_id            INTEGER → products.id, INDEX              │
│     quantity              INTEGER DEFAULT 1                          │
│     selected_color        VARCHAR(50) NULLABLE                       │
│     selected_size         VARCHAR(20) NULLABLE                       │
│     created_at            DATETIME                                   │
│     updated_at            DATETIME                                   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                          ORDERS TABLE                                │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│     order_number          VARCHAR(50) UNIQUE, INDEX                  │
│ FK  user_id               INTEGER → users.id, INDEX, NULLABLE       │
│     guest_email           VARCHAR(255) INDEX, NULLABLE               │
│     shipping_name         VARCHAR(255)                                │
│     shipping_address      TEXT                                       │
│     shipping_city         VARCHAR(100)                               │
│     shipping_state        VARCHAR(100)                                │
│     shipping_zip          VARCHAR(20)                                │
│     shipping_country      VARCHAR(100) DEFAULT 'USA'                │
│     shipping_phone        VARCHAR(20) NULLABLE                       │
│     subtotal              NUMERIC(10,2)                              │
│     tax                   NUMERIC(10,2) DEFAULT 0.0                  │
│     shipping_cost          NUMERIC(10,2) DEFAULT 0.0                  │
│     total                 NUMERIC(10,2)                              │
│     status                VARCHAR(50) DEFAULT 'pending', INDEX      │
│                          (pending, processing, shipped,              │
│                           delivered, cancelled)                       │
│     created_at            DATETIME, INDEX                            │
│     updated_at            DATETIME                                   │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
                             │ 1:N
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐
│ ORDER_ITEMS │    │   PAYMENTS   │
└──────────────┘    └──────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       ORDER_ITEMS TABLE                              │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│ FK  order_id              INTEGER → orders.id, INDEX                 │
│ FK  product_id            INTEGER → products.id                     │
│     quantity              INTEGER                                    │
│     price                 NUMERIC(10,2)  (price at time of order)   │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        PAYMENTS TABLE                                │
├─────────────────────────────────────────────────────────────────────┤
│ PK  id                    INTEGER                                    │
│ FK  order_id              INTEGER → orders.id, INDEX                 │
│     payment_method        VARCHAR(50)                                │
│                          (stripe, paypal, etc.)                      │
│     payment_intent_id     VARCHAR(255) NULLABLE                       │
│     amount                NUMERIC(10,2)                              │
│     currency              VARCHAR(10) DEFAULT 'USD'                  │
│     status                VARCHAR(50) DEFAULT 'pending', INDEX        │
│                          (pending, completed, failed, refunded)      │
│     transaction_id        VARCHAR(255) UNIQUE, INDEX                  │
│     created_at            DATETIME, INDEX                            │
│     updated_at            DATETIME                                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔍 Vector Database (ChromaDB) Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                    CHROMADB COLLECTION                               │
│                  "insightshop_products"                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  DOCUMENT STRUCTURE:                                                  │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ ID: "product_{product_id}"                                    │   │
│  │                                                               │   │
│  │ DOCUMENT TEXT:                                                │   │
│  │ "{name} {description} Category: {category}                    │   │
│  │  Color: {color} Size: {size} Price: ${price}"                │   │
│  │                                                               │   │
│  │ METADATA:                                                      │   │
│  │ {                                                              │   │
│  │   "product_id": <integer>,                                    │   │
│  │   "name": "<product name>",                                    │   │
│  │   "category": "<men/women/kids>",                             │   │
│  │   "color": "<color>",                                          │   │
│  │   "price": "<price as string>"                                 │   │
│  │ }                                                              │   │
│  │                                                               │   │
│  │ EMBEDDING:                                                     │   │
│  │ [vector of floats - generated by ChromaDB]                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                       │
│  SEARCH METHOD:                                                       │
│  • Cosine Similarity (hnsw:space = "cosine")                         │
│  • Query text is embedded and compared to product embeddings         │
│  • Returns top N most similar products                               │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🧠 Knowledge Base Structure

```
┌─────────────────────────────────────────────────────────────────────┐
│                    FASHION KNOWLEDGE BASE                            │
│                    (utils/fashion_kb.py)                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  1. COLOR MATCHING                                                   │
│     • Basics: Neutral, Complementary, Analogous, Monochromatic      │
│     • By Color: Specific advice for each color                       │
│     • Classic Combinations: Navy & White, Black & White, etc.        │
│                                                                       │
│  2. STYLE ADVICE                                                      │
│     • Fit Guidelines                                                 │
│     • Layering Techniques                                            │
│     • Proportions & Balance                                           │
│                                                                       │
│  3. OCCASIONS                                                         │
│     • business_formal                                                │
│     • business_casual                                                 │
│     • casual                                                          │
│     • date_night                                                      │
│     • wedding                                                         │
│     • outdoor_active                                                  │
│     • summer                                                          │
│     • winter                                                          │
│                                                                       │
│  4. FABRIC GUIDE                                                      │
│     • cotton, polyester, wool, silk, linen, denim, cashmere, blend  │
│     • Each includes: description, care, best_for, characteristics   │
│                                                                       │
│  5. DRESS STYLES                                                      │
│     • Necklines: scoop, v-neck, round, boat, halter, etc.            │
│     • Features: bow, padding, slit, peplum, wrap, a-line, etc.       │
│     • Men's Styles: v-neck, crew, henley, polo                       │
│                                                                       │
│  6. STYLING TIPS                                                      │
│     • Building a Wardrobe                                             │
│     • Accessories                                                     │
│     • Seasonal Transitions                                            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow: AI Chat Request

```
┌─────────────┐
│   User      │
│  "Show me   │
│  blue shirts│
│  for men"   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend (AIChat.js)                                        │
│ • Captures user input                                       │
│ • Maintains conversation history                            │
│ • Sends POST /api/ai/chat                                   │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ HTTP POST
       │ { message, history, selected_product_ids }
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Backend (routes/ai_agent.py)                                │
│                                                              │
│ STEP 1: Intent Detection                                    │
│   • detected_category = "men"                               │
│   • detected_color = "blue"                                 │
│   • detected_clothing_type = "Shirt"                        │
│                                                              │
│ STEP 2: Search Strategy                                     │
│   • Since strict filters detected → Direct SQL Query        │
│   • Query: WHERE category='men' AND                          │
│            (color LIKE '%blue%' OR name LIKE '%blue%') AND   │
│            (clothing_type LIKE '%Shirt%' OR                  │
│             clothing_type LIKE '%T-Shirt%' OR               │
│             name LIKE '%Shirt%')                            │
│                                                              │
│ STEP 3: Context Building                                    │
│   • Get matching products (e.g., 15 products found)        │
│   • Load fashion knowledge base                             │
│   • Build system prompt:                                    │
│     - Fashion knowledge (color matching, fabrics)          │
│     - Product database context                              │
│     - Styling guidelines                                    │
│   • Build user prompt:                                      │
│     - User message                                          │
│     - Found products list with IDs                          │
│                                                              │
│ STEP 4: LLM Call (AWS Bedrock)                              │
│   • Send prompt to Claude 3 Sonnet                          │
│   • Receive natural language response                       │
│                                                              │
│ STEP 5: Response Formatting                                 │
│   • Extract product IDs from response                       │
│   • Set action = "search_results"                          │
│   • Return JSON:                                            │
│     {                                                       │
│       response: "I found 15 blue shirts...",              │
│       suggested_products: [...],                           │
│       suggested_product_ids: [1, 5, 12, ...],             │
│       action: "search_results"                             │
│     }                                                       │
└──────┬───────────────────────────────────────────────────────┘
       │
       │ HTTP Response
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Frontend (AIChat.js)                                        │
│ • Display AI response in chat                               │
│ • If action == "search_results":                            │
│   - Navigate to products page OR                            │
│   - Update product grid inline                              │
│ • Show suggested products                                   │
└─────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend AI Components
- **Flask** - Web framework
- **AWS Bedrock** - LLM service (Claude 3 Sonnet/Haiku)
- **ChromaDB** - Vector database for semantic search
- **SQLAlchemy** - ORM for relational database
- **Boto3** - AWS SDK for Bedrock and Polly
- **Sentence Transformers** - Embeddings (via ChromaDB)

### Frontend AI Components
- **React** - UI framework
- **Axios** - HTTP client
- **Web Speech API** - Voice input/output
- **AWS Polly** - Text-to-speech (optional)

### Database
- **SQLite** - Relational database (products, users, orders, etc.)
- **ChromaDB** - Vector database (semantic product search)

## 📊 Key Features

### 1. Multi-Layer Search Strategy
- **Strict Filters**: Direct SQL queries when specific criteria detected
- **Semantic Search**: Vector search for natural language queries
- **Hybrid Approach**: Combines both for best results

### 2. Context-Aware AI
- **Product Context**: Full product database available to AI
- **Fashion Knowledge**: Comprehensive styling and fashion advice
- **Conversation History**: Maintains context across messages

### 3. Intelligent Intent Detection
- Category detection (men/women/kids)
- Color extraction (with normalization)
- Clothing type recognition
- Occasion and age group identification
- Dress style features

### 4. Product Comparison
- Automatic comparison when requested
- Price analysis
- Feature comparison
- Best value recommendations

## 🔐 Security & Configuration

### Environment Variables
```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...

# Bedrock Model
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0

# Database
DB_PATH=insightshop.db
VECTOR_DB_PATH=./vector_db

# JWT
JWT_SECRET=...
```

### Fallback Behavior
- If Bedrock not configured: Returns helpful setup message
- If ChromaDB not available: Falls back to SQL search
- Graceful degradation at each layer

