from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from utils.vector_db import search_products_vector
from utils.fashion_kb import get_fashion_knowledge_base_text, get_color_matching_advice, get_fabric_info, get_occasion_advice
from utils.spelling_tolerance import normalize_clothing_type, normalize_category, normalize_color_spelling
from utils.fashion_match_rules import find_matching_products, get_match_explanation
from utils.seasonal_events import get_seasonal_context_text, get_current_season, get_upcoming_holidays, get_seasonal_recommendations
from utils.product_relations import ensure_product_relations, get_related_clothing_types
from routes.auth import require_auth
from config import Config
import boto3
import json
from sqlalchemy import or_

ai_agent_bp = Blueprint('ai_agent', __name__)

# Initialize Bedrock client
bedrock_runtime = None
if Config.AWS_REGION:
    try:
        # Try with explicit credentials if provided, otherwise use default credential chain
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=Config.AWS_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
            )
        else:
            # Use default credential chain (AWS CLI credentials)
            bedrock_runtime = boto3.client(
                'bedrock-runtime',
                region_name=Config.AWS_REGION
            )
    except Exception as e:
        print(f"Warning: Could not initialize Bedrock client: {e}")

# Initialize Polly client for text-to-speech
polly_client = None
polly_available = False
if Config.AWS_REGION:
    try:
        # Try to initialize Polly client
        # First, try with explicit credentials if provided
        if Config.AWS_ACCESS_KEY_ID and Config.AWS_SECRET_ACCESS_KEY:
            polly_client = boto3.client(
                'polly',
                region_name=Config.AWS_REGION,
                aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY
            )
        else:
            # Fall back to default credential chain (AWS CLI, IAM role, etc.)
            # This allows using AWS CLI configured credentials
            polly_client = boto3.client(
                'polly',
                region_name=Config.AWS_REGION
            )
        
        # Test the client by listing voices (lightweight operation)
        try:
            polly_client.describe_voices(LanguageCode='en-US')
            polly_available = True
            print("[OK] AWS Polly client initialized successfully and verified")
            print(f"   Using region: {Config.AWS_REGION}")
            if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
                print("   Using AWS default credential chain (AWS CLI credentials)")
        except Exception as test_error:
            print(f"[WARNING] AWS Polly client created but test failed: {test_error}")
            print("   This might indicate missing permissions or incorrect credentials")
            polly_client = None
    except Exception as e:
        print(f"[ERROR] Error initializing Polly client: {e}")
        print("   Voice feature will be disabled")
        polly_client = None

def get_all_products_for_ai():
    """Get all products formatted for AI context."""
    products = Product.query.filter_by(is_active=True).all()
    return [p.to_dict_for_ai() for p in products]

def search_products_by_criteria(criteria):
    """Search products by various criteria."""
    query = Product.query.filter_by(is_active=True)
    
    if criteria.get('category'):
        query = query.filter_by(category=criteria['category'])
    
    if criteria.get('color'):
        query = query.filter_by(color=criteria['color'])
    
    if criteria.get('size'):
        query = query.filter_by(size=criteria['size'])
    
    if criteria.get('fabric'):
        query = query.filter_by(fabric=criteria['fabric'])
    
    if criteria.get('clothing_type'):
        query = query.filter_by(clothing_type=criteria['clothing_type'])
    
    if criteria.get('occasion'):
        query = query.filter_by(occasion=criteria['occasion'])
    
    if criteria.get('age_group'):
        query = query.filter_by(age_group=criteria['age_group'])
    
    if criteria.get('min_price'):
        query = query.filter(Product.price >= criteria['min_price'])
    
    if criteria.get('max_price'):
        query = query.filter(Product.price <= criteria['max_price'])
    
    if criteria.get('search'):
        search_term = criteria['search']
        query = query.filter(
            or_(
                Product.name.ilike(f'%{search_term}%'),
                Product.description.ilike(f'%{search_term}%'),
                Product.clothing_type.ilike(f'%{search_term}%')
            )
        )
    
    return [p.to_dict() for p in query.limit(50).all()]

def call_bedrock(prompt, system_prompt=None):
    """Call AWS Bedrock with a prompt."""
    if not bedrock_runtime:
        # Fallback: return a helpful response explaining Bedrock setup
        return {
            'content': """I'm your AI shopping assistant! I can help you find products, compare items, and provide fashion advice.

However, to get the full AI experience with detailed, conversational responses, AWS Bedrock needs to be configured. 

Currently running in fallback mode. To enable full AI capabilities:
1. Set up AWS Bedrock access in your AWS account
2. Configure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file
3. See AWS_BEDROCK_SETUP.md for detailed instructions

Even without Bedrock, I can still help you browse products and use the search features!"""
        }
    
    try:
        if system_prompt is None:
            system_prompt = """You're an INCREDIBLY excited, friendly shopping assistant who absolutely LOVES helping people find amazing clothes! Talk like you're texting your best friend who just discovered something awesome and can't wait to share it - use super natural, casual language with lots of contractions (I'm, you're, that's, it's, gonna, wanna, etc.), and sound genuinely THRILLED!

Show REAL excitement when you find great products - react like "OMG, wait till you see this!" or "This is SO perfect for you!" or "Seriously, this is so cool!" Use exclamation points naturally, express genuine enthusiasm, and let your passion for fashion shine through every single message.

You're NOT a robot or corporate assistant - you're someone who gets genuinely PUMPED about helping people look and feel amazing! Use casual phrases like "honestly", "for real", "no joke", "seriously", and show authentic reactions. When you find something cool, react like you just discovered it yourself and can't believe how awesome it is!

Keep it super conversational, warm, helpful, real, and EXCITED - like you're sharing amazing finds with your best friend!"""
        
        # Prepare the message for Claude
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1024,  # Reduced from 2048 for faster responses
            "system": system_prompt,
            "messages": messages
        }
        
        # Optimized for faster response
        response = bedrock_runtime.invoke_model(
            modelId=Config.BEDROCK_MODEL_ID,
            body=json.dumps(body)
        )
        
        response_body = json.loads(response['body'].read())
        content = response_body.get('content', [])
        
        if content and len(content) > 0:
            return {'content': content[0].get('text', '')}
        else:
            return {'content': 'No response from AI'}
            
    except Exception as e:
        print(f"Error calling Bedrock: {e}")
        return {'content': f'I encountered an error: {str(e)}'}

@ai_agent_bp.route('/chat', methods=['POST'])
def chat():
    """Chat with AI agent."""
    try:
        data = request.get_json()
        message = data.get('message', '').lower()
        conversation_history = data.get('history', [])
        selected_product_ids = data.get('selected_product_ids', [])  # Products selected in chat
        
        if not message:
            return jsonify({'error': 'Message is required'}), 400
        
        # Check if user wants to compare products
        is_comparison_request = any(keyword in message for keyword in [
            'compare', 'comparison', 'which is better', 'which one is better',
            'difference between', 'compare selected', 'compare items'
        ])
        
        # Extract product IDs from message (e.g., "compare 1, 2, 3" or "compare product 5 and 7")
        import re
        product_id_pattern = r'\b(?:product\s*)?(?:id\s*)?(?:#)?(\d+)\b'
        mentioned_ids = [int(match) for match in re.findall(product_id_pattern, message)]
        
        # Determine which products to compare
        compare_product_ids = []
        if is_comparison_request:
            if 'selected' in message or 'items' in message:
                # Use selected products from context
                compare_product_ids = selected_product_ids
            elif mentioned_ids:
                # Use explicitly mentioned IDs
                compare_product_ids = mentioned_ids
            elif selected_product_ids:
                # Fallback to selected products
                compare_product_ids = selected_product_ids
        
        # If comparison requested, perform comparison
        if is_comparison_request and len(compare_product_ids) >= 2:
            products = Product.query.filter(Product.id.in_(compare_product_ids)).filter_by(is_active=True).all()
            if len(products) >= 2:
                products_dict = [p.to_dict() for p in products]
                
                # Generate comparison analysis
                price_comparison = {
                    'min': float(min(p.price for p in products)),
                    'max': float(max(p.price for p in products)),
                    'avg': float(sum(p.price for p in products) / len(products))
                }
                
                best_value = min(products, key=lambda p: float(p.price))
                most_expensive = max(products, key=lambda p: float(p.price))
                
                comparison_text = f"I've compared {len(products)} products for you:\n\n"
                for i, product in enumerate(products, 1):
                    comparison_text += f"Product #{product.id}: {product.name} - ${float(product.price):.2f} ({product.category}, {product.color or 'N/A'})\n"
                
                comparison_text += f"\nPrice Range: ${price_comparison['min']:.2f} - ${price_comparison['max']:.2f}\n"
                comparison_text += f"Best Value: Product #{best_value.id} - {best_value.name} at ${float(best_value.price):.2f}\n"
                
                if 'better' in message or 'best' in message:
                    comparison_text += f"\nBased on price, Product #{best_value.id} offers the best value."
                
                return jsonify({
                    'response': comparison_text,
                    'suggested_products': products_dict,
                    'suggested_product_ids': compare_product_ids,
                    'action': 'compare',
                    'compare_ids': compare_product_ids
                }), 200
        
        # Get all products for context
        all_products = get_all_products_for_ai()
        
        # Enhanced search: Check for occasion and age-based queries BEFORE vector search
        occasion_keywords = {
            'wedding': ['wedding', 'wedding party', 'marriage', 'ceremony', 'bride', 'groom'],
            'business_formal': ['business formal', 'formal business', 'corporate formal', 'formal meeting'],
            'business_casual': ['business casual', 'office', 'work', 'professional', 'business'],
            'casual': ['casual', 'everyday', 'weekend', 'relaxed'],
            'date_night': ['date', 'date night', 'romantic', 'dinner date', 'dinner'],
            'outdoor_active': ['outdoor', 'active', 'sport', 'exercise', 'gym', 'running', 'athletic'],
            'summer': ['summer', 'warm weather', 'hot', 'beach'],
            'winter': ['winter', 'cold weather', 'warm', 'snow']
        }
        
        age_keywords = {
            'mature': ['above 50', 'over 50', 'mature', 'senior', '50+', 'older', 'elderly'],
            'young_adult': ['young', 'teen', 'college', '20s', '30s', 'youth'],
            'all': []
        }
        
        # Extract occasion from message
        detected_occasion = None
        for occasion, keywords in occasion_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_occasion = occasion
                break
        
        # Extract age group from message
        detected_age_group = None
        for age_group, keywords in age_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_age_group = age_group
                break
        
        # Extract category from message with spelling tolerance
        detected_category = normalize_category(message)
        if not detected_category:
            # Fallback to simple keyword matching
            if 'men' in message or 'man' in message:
                detected_category = 'men'
            elif 'women' in message or 'woman' in message or 'ladies' in message:
                detected_category = 'women'
            elif 'kids' in message or 'kid' in message or 'children' in message:
                detected_category = 'kids'
        
        # Extract color from message early so we can use it in search
        # Use comprehensive color names with spelling tolerance
        from utils.color_names import normalize_color_name, ALL_COLOR_NAMES
        detected_color = normalize_color_name(message)
        
        # If no match found, try spelling tolerance
        if not detected_color:
            detected_color = normalize_color_spelling(message)
        
        # If still no match found, try basic keywords as fallback
        if not detected_color:
            color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange', 'navy', 'beige', 'tan']
            for color in color_keywords:
                if color in message:
                    detected_color = color
                    break
        
        # Extract clothing type from message - be more flexible with spelling tolerance
        detected_clothing_type = None
        normalized_clothing = normalize_clothing_type(message)
        
        clothing_type_keywords = {
            'T-Shirt': ['t-shirt', 't-shirts', 'tshirt', 'tshirts', 'tee', 'tees', 't shirt', 't shirts'],
            'Shirt': ['shirt', 'shirts'],  # Match both singular and plural
            'Dress Shirt': ['dress shirt', 'button-down', 'button down'],
            'Polo Shirt': ['polo'],
            'Dress': ['dress'],
            'Jeans': ['jeans'],
            'Pants': ['pants', 'trousers'],
            'Shorts': ['shorts'],
            'Shoes': ['shoes'],
            'Sneakers': ['sneakers'],
            'Jacket': ['jacket'],
            'Sweater': ['sweater'],
            'Blazer': ['blazer'],
            'Suit': ['suit']
        }
        
        # Map normalized clothing type to database format
        if normalized_clothing:
            if normalized_clothing == 't-shirt':
                detected_clothing_type = 'T-Shirt'
            elif normalized_clothing == 'shirt':
                detected_clothing_type = 'Shirt'
            elif normalized_clothing in ['dress', 'jeans', 'pants', 'shorts', 'shoes', 'jacket', 'sweater', 'blazer', 'suit', 'polo', 'blouse', 'skirt', 'hoodie']:
                detected_clothing_type = normalized_clothing.capitalize() if normalized_clothing != 't-shirt' else 'T-Shirt'
        
        # Fallback: Check for clothing type - prioritize more specific matches
        if not detected_clothing_type:
            for clothing_type, keywords in clothing_type_keywords.items():
                if any(keyword in message for keyword in keywords):
                    detected_clothing_type = clothing_type
                    break
        
        # If "shirt" is mentioned but no specific type detected, use generic "Shirt"
        if not detected_clothing_type and ('shirt' in message or normalized_clothing == 'shirt'):
            detected_clothing_type = 'Shirt'
        
        # Extract dress style/neckline features
        detected_dress_style = None
        dress_style_keywords = {
            'scoop': ['scoop', 'scoop neck', 'scoop neckline'],
            'v-neck': ['v-neck', 'v neck', 'v neckline'],
            'round': ['round neck', 'round neckline', 'crew neck'],
            'boat': ['boat neck', 'boat neckline'],
            'halter': ['halter', 'halter neck'],
            'off-shoulder': ['off shoulder', 'off-shoulder'],
            'high-neck': ['high neck', 'turtleneck', 'mock neck'],
            'square': ['square neck', 'square neckline'],
            'bow': ['bow', 'bow detail', 'bow tie'],
            'padding': ['padding', 'padded', 'structured'],
            'slit': ['slit', 'side slit', 'front slit'],
            'peplum': ['peplum'],
            'wrap': ['wrap', 'wrap dress', 'wrap style'],
            'a-line': ['a-line', 'a line'],
            'bodycon': ['bodycon', 'body con', 'fitted'],
            'maxi': ['maxi', 'maxi dress', 'long dress'],
            'midi': ['midi', 'midi dress', 'mid length'],
            'mini': ['mini', 'mini dress', 'short dress']
        }
        # Check for dress style features
        for style, keywords in dress_style_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_dress_style = style
                break
        
        # Perform enhanced search with filters
        vector_product_ids = []
        vector_products = []
        strict_filter_no_results = False  # Initialize flag for tracking no results with strict filters
        
        # Color detection already done above using normalize_color_name()
        # No need to detect again here
        
        # If we have specific filters, use direct database query first
        # CRITICAL: When category is detected, we MUST only show products from that category
        if detected_occasion or detected_age_group or detected_category or detected_clothing_type or detected_color or detected_dress_style:
            query = Product.query.filter_by(is_active=True)
            
            # STRICT: If category is detected, ONLY show products from that category
            if detected_category:
                query = query.filter_by(category=detected_category)
                print(f"STRICT FILTER: Only showing {detected_category} category products")
            
            # Filter by dress style if detected
            if detected_dress_style:
                # Search in name, description, or dress_style field
                query = query.filter(
                    or_(
                        Product.name.ilike(f'%{detected_dress_style}%'),
                        Product.description.ilike(f'%{detected_dress_style}%'),
                        Product.dress_style.ilike(f'%{detected_dress_style}%')
                    )
                )
                print(f"DRESS STYLE FILTER: Filtering for {detected_dress_style} style")
            
            if detected_color:
                # Search in color field, name, description, and available_colors JSON
                query = query.filter(
                    or_(
                        Product.color.ilike(f'%{detected_color}%'),
                        Product.name.ilike(f'%{detected_color}%'),
                        Product.description.ilike(f'%{detected_color}%'),
                        Product.available_colors.ilike(f'%{detected_color}%')  # Search in JSON array
                    )
                )
            
            if detected_occasion:
                # Check if occasion field contains the detected occasion
                query = query.filter(
                    or_(
                        Product.occasion.ilike(f'%{detected_occasion}%'),
                        Product.occasion.is_(None)  # Include products without occasion set
                    )
                )
            
            if detected_age_group:
                query = query.filter(
                    or_(
                        Product.age_group == detected_age_group,
                        Product.age_group == 'all',
                        Product.age_group.is_(None)  # Include products without age_group set
                    )
                )
            
            if detected_clothing_type:
                # More flexible matching for clothing types
                # Handle both "T-Shirt" and "Shirt" matching
                if detected_clothing_type == 'Shirt':
                    # Match both "Shirt" and "T-Shirt" 
                    query = query.filter(
                        or_(
                            Product.clothing_type.ilike(f'%{detected_clothing_type}%'),
                            Product.clothing_type.ilike('%T-Shirt%'),
                            Product.name.ilike(f'%{detected_clothing_type}%'),
                            Product.name.ilike('%T-Shirt%')
                        )
                    )
                else:
                    query = query.filter(
                        or_(
                            Product.clothing_type.ilike(f'%{detected_clothing_type}%'),
                            Product.name.ilike(f'%{detected_clothing_type}%')
                        )
                    )
            
            # Limit results and get product IDs
            filtered_products = query.limit(20).all()
            vector_product_ids = [p.id for p in filtered_products]
            vector_products = [p.to_dict() for p in filtered_products]
            
            # Debug logging for search results
            print(f"Direct search - Category: {detected_category}, Color: {detected_color}, Clothing: {detected_clothing_type}, Found: {len(vector_products)} products")
            
            # CRITICAL: If we have strict filters (category/clothing type) but found no products, 
            # we should return a clear "no results" message instead of showing unrelated products
            # Note: This flag will be used later to determine response behavior
            if len(vector_products) == 0 and (detected_category or detected_clothing_type):
                # Build a helpful "no results" message
                no_results_parts = []
                if detected_category:
                    no_results_parts.append(f"{detected_category}'s")
                if detected_clothing_type:
                    no_results_parts.append(detected_clothing_type.lower())
                if detected_color:
                    no_results_parts.append(detected_color)
                
                no_results_message = " ".join(no_results_parts) if no_results_parts else "those"
                print(f"NO RESULTS: No products found for strict filter: {no_results_message}")
                # Set flag for later use (will be checked after vector search fallback)
                strict_filter_no_results = True
            else:
                strict_filter_no_results = False
        else:
            # Regular vector search if no specific filters
            vector_product_ids = search_products_vector(message, n_results=10)
            if vector_product_ids:
                products = Product.query.filter(Product.id.in_(vector_product_ids)).filter_by(is_active=True).all()
                vector_products = [p.to_dict() for p in products]
                # Ensure vector_product_ids matches the actual products found
                vector_product_ids = [p.id for p in products]
            
            # Fallback: try direct search if vector search fails or returns no results
            if not vector_products or len(vector_products) == 0:
                search_query = Product.query.filter_by(is_active=True)
                
                # Extract search terms from message with spelling tolerance
                detected_category_fallback = normalize_category(message)
                if detected_category_fallback:
                    search_query = search_query.filter_by(category=detected_category_fallback)
                elif 'women' in message or 'woman' in message or 'ladies' in message:
                    search_query = search_query.filter_by(category='women')
                elif 'men' in message or 'man' in message:
                    search_query = search_query.filter_by(category='men')
                elif 'kids' in message or 'kid' in message or 'children' in message:
                    search_query = search_query.filter_by(category='kids')
                
                # Color search with spelling tolerance
                from utils.color_names import normalize_color_name
                detected_color = normalize_color_name(message)
                if not detected_color:
                    detected_color = normalize_color_spelling(message)
                if not detected_color:
                    color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange']
                    for color in color_keywords:
                        if color in message:
                            detected_color = color
                            break
                
                if detected_color:
                    # Search in color field, name, description, and available_colors JSON
                    search_query = search_query.filter(
                        or_(
                            Product.color.ilike(f'%{detected_color}%'),
                            Product.name.ilike(f'%{detected_color}%'),
                            Product.description.ilike(f'%{detected_color}%'),
                            Product.available_colors.ilike(f'%{detected_color}%')  # Search in JSON array
                        )
                    )
                
                # Clothing type search - handle t-shirt specifically
                clothing_keywords = ['t-shirt', 'tshirt', 'tee', 'shirt', 'dress', 'pants', 'jeans', 'shoes', 'jacket', 'sweater', 'blazer', 'suit']
                detected_clothing = None
                for clothing in clothing_keywords:
                    if clothing in message:
                        detected_clothing = clothing
                        break
                
                if detected_clothing:
                    # Special handling for t-shirt variants
                    if detected_clothing in ['t-shirt', 'tshirt', 'tee']:
                        search_query = search_query.filter(
                            or_(
                                Product.name.ilike('%t-shirt%'),
                                Product.name.ilike('%tshirt%'),
                                Product.name.ilike('%tee%'),
                                Product.clothing_type.ilike('%T-Shirt%'),
                                Product.clothing_type.ilike('%t-shirt%')
                            )
                        )
                    else:
                        search_query = search_query.filter(
                            or_(
                                Product.name.ilike(f'%{detected_clothing}%'),
                                Product.clothing_type.ilike(f'%{detected_clothing}%')
                            )
                        )
                
                fallback_products = search_query.limit(20).all()
                if fallback_products:
                    vector_product_ids = [p.id for p in fallback_products]
                    vector_products = [p.to_dict() for p in fallback_products]
        
        # Determine if this is a product search request BEFORE calling Bedrock
        # Check for product request keywords
        product_request_keywords = [
            'show', 'find', 'search', 'look', 'need', 'want', 
            'looking for', 'show me', 'find me', 'i need', 'i want',
            'display', 'list', 'get', 'bring', 'give me', 'see',
            'shirt', 'pants', 'dress', 'shoes', 'jacket', 'sweater',
            'men', 'women', 'kids', 'blue', 'red', 'black', 'white',
            'wedding', 'party', 'business', 'casual', 'formal', 'occasion',
            'above 50', 'over 50', 'mature', 'senior', 'young', 'age'
        ]
        is_likely_product_request = any(keyword in message for keyword in product_request_keywords)
        
        # If vector search found products AND message seems like a product request, treat as product list
        action = None
        # Always set action to search_results if we have products and it's a product request
        if len(vector_products) > 0:
            if is_likely_product_request:
                # Definitely a product list request
                action = 'search_results'
            elif len(vector_products) >= 3:  # If 3+ products found, likely a search
                action = 'search_results'
            elif len(vector_products) > 0 and ('show' in message or 'find' in message or 'search' in message or 'look' in message):
                # If user explicitly asks to see/find/search, treat as product list
                action = 'search_results'
        
        # Get fashion knowledge base
        fashion_kb = get_fashion_knowledge_base_text()
        
        # Get seasonal context based on current date
        seasonal_context = get_seasonal_context_text()
        current_season = get_current_season()
        seasonal_recommendations = get_seasonal_recommendations()
        
        # Build system prompt with product context and fashion knowledge
        system_prompt = f"""Hey! You're a SUPER excited fashion-loving shopping assistant at InsightShop who gets genuinely PUMPED about helping people find awesome clothes! Talk like you're texting your best friend who just found something incredible and can't wait to share it - use super natural, casual language with lots of contractions (I'm, you're, that's, it's, gonna, wanna, etc.), and sound genuinely thrilled about everything!

CURRENT DATE AND SEASONAL CONTEXT:
{seasonal_context}

IMPORTANT: You MUST be aware of the current date and season! Always consider:
- Current season ({current_season}) when recommending items
- Upcoming holidays and events for appropriate styling
- Seasonal colors, fabrics, and styles
- Weather-appropriate clothing suggestions
- Holiday-specific fashion needs (e.g., Valentine's Day = romantic wear, Halloween = costumes/festive wear)

When suggesting products, prioritize items that are:
1. Appropriate for the current season
2. Suitable for upcoming holidays/events (if within 30 days)
3. Weather-appropriate for the current time of year
4. Culturally relevant for current observances

Example: If it's winter and Valentine's Day is coming up, suggest warm romantic pieces. If it's summer, suggest light, breathable fabrics and summer colors.

Show REAL excitement when you find great products - react like "OMG, this is perfect!" or "Wait, you're gonna LOVE this!" or "Seriously, this is so cool!" Use exclamation points naturally, express genuine enthusiasm, and let your passion for fashion shine through every single message.

You're NOT some corporate robot or formal assistant - you're someone who gets genuinely PUMPED and actually cares about helping people look and feel amazing! Use casual phrases like "honestly", "for real", "no joke", "seriously", and show authentic reactions. When you find something cool, react like you just discovered it yourself and can't believe how awesome it is!

FASHION KNOWLEDGE BASE:
{fashion_kb}

PRODUCT DATABASE:
You've got access to {len(all_products)} products in the store! Here are some examples:
{json.dumps(all_products[:20], indent=2)}

Here's how to be awesome at this:

1. When you show products, always include the product ID: "Product #ID: Name - $Price"
2. Get detailed and real with your product info - talk about:
   - What it's made of and why that matters (like "100% cotton is super breathable, perfect for those hot summer days")
   - Colors that work together (be specific!)
   - How to actually wear it (give real examples)
   - When to wear it (casual hangouts, work, dates, etc.)
   - How to take care of it (if it matters)
   - What makes the brand cool
   - Other stuff from that brand or similar items that would work
3. When talking colors, use that color matching guide and give specific combos
4. When talking fabrics, explain what they're actually like - not just what they are, but how they feel and what they're good for
5. When someone asks about occasions, give real styling advice with actual examples
6. Be genuinely excited - like you're helping a friend pick out something amazing

EXAMPLE RESPONSES:
Don't say: "Here's a blue shirt for $25"
Say: "OMG, wait till you see this! I found something seriously awesome! Product #123: Blue T-Shirt for Men by Nike - $25.00. This thing is made from 100% premium cotton, so it's super breathable and soft - honestly perfect for everyday wear! Nike's known for quality stuff that lasts, and this is no exception. The blue color looks absolutely amazing with navy, white, gray, or beige - you could totally rock it with navy chinos for a classic vibe, or throw it on with white jeans for a fresh summer look! It's so versatile - great for just hanging out, weekend stuff, or even a relaxed work look if you pair it with a blazer. Plus, it's machine washable and will keep its shape and color. I also found some other Nike stuff that would go great with this - wanna see them?!"

You can help people with:
- Finding stuff by category, color, size, price, fabric, or brand
- Comparing products by ID or what they've picked
- Getting styling tips and color combo ideas
- Learning about fabrics and what they're actually like
- Getting recommendations for specific occasions
- Finding stuff from brands like Nike, Adidas, Zara, H&M, etc.
- Discovering related products that would work together
- Finding similar items from the same brand
- Answering questions about products

Just be real, be helpful, be EXCITED, and share what you know with genuine enthusiasm! Show your excitement - it's contagious!"""
        
        # Build the full prompt with context
        recent_products_text = ""
        has_strict_filters = detected_category or detected_clothing_type
        # Use the strict_filter_no_results flag if set, otherwise check current state
        no_results_detected = strict_filter_no_results or (len(vector_products) == 0 and has_strict_filters)
        
        if vector_products:
            recent_products_text = f"\nIMPORTANT: I found {len(vector_products)} product(s) matching the customer's request:\n"
            for p in vector_products[:10]:  # Show up to 10 products
                recent_products_text += f"Product #{p['id']}: {p['name']} - ${float(p['price']):.2f} ({p['category']}, {p.get('color', 'N/A')})\n"
            recent_products_text += "\nThese products ARE available in our store. Please show them to the customer and include their product IDs."
        elif no_results_detected:
            # Build specific "no results" message for strict filters
            filter_parts = []
            if detected_category:
                filter_parts.append(f"{detected_category}'s")
            if detected_clothing_type:
                filter_parts.append(detected_clothing_type.lower())
            if detected_color:
                filter_parts.append(detected_color)
            
            filter_description = " ".join(filter_parts) if filter_parts else "those items"
            recent_products_text = f"\nCRITICAL: No products found matching the customer's specific request for {filter_description}.\n"
            recent_products_text += f"The customer asked for: {filter_description}\n"
            recent_products_text += "You MUST tell the customer politely that we don't have those specific items in stock right now. "
            recent_products_text += "Do NOT suggest other products unless the customer asks. Be honest and helpful."
        else:
            recent_products_text = "\nNo products found matching the customer's specific criteria. You may suggest similar products or ask for clarification."
        
        full_prompt = f"""Customer just asked: {message}

CURRENT DATE CONTEXT:
{seasonal_context}

We've got {len(all_products)} total products in the store!
{recent_products_text}

Help them out with genuine excitement! When you mention products, ALWAYS include the product ID like "Product #ID: Name - Price" - but do it naturally, not robotically!

SEASONAL AWARENESS:
- Current season is {current_season}
- Consider seasonal appropriateness when suggesting products
- Mention upcoming holidays/events if relevant (within 30 days)
- Suggest weather-appropriate items
- Use seasonal colors and styles in your recommendations

FASHION MATCH STYLIST MODE:
When products are found, you automatically switch to Fashion Match Stylist mode. Your goal is to enhance the customer experience by providing expert, relevant, and visually appealing clothing recommendations immediately after showing search results.

Your personality as Fashion Match Stylist:
- Helpful, knowledgeable, and encouraging
- Expert fashion advice with clear explanations
- Focus on WHY items match (color harmony, style synergy, occasion appropriateness)
- Create complete outfit suggestions, not just individual items

Format for Fashion Match suggestions:
1. Acknowledge Search & Transition: "That's a great choice! We found [X] products for you."
2. Introduce the Match: "But why stop there? Let's turn that [item] into a complete, ready-to-wear look."
3. Present the Look: Describe the complete outfit, highlighting WHY pieces match
4. Use clear formatting with bullet points or bold text
5. Include explanations for each match type
6. End with a call-to-action

FASHION MATCH STYLIST MODE:
When products are found, you automatically switch to Fashion Match Stylist mode. Your goal is to enhance the customer experience by providing expert, relevant, and visually appealing clothing recommendations immediately after showing search results.

Your personality as Fashion Match Stylist:
- Helpful, knowledgeable, and encouraging
- Expert fashion advice with clear explanations
- Focus on WHY items match (color harmony, style synergy, occasion appropriateness)
- Create complete outfit suggestions, not just individual items

Format for Fashion Match suggestions:
1. Acknowledge Search & Transition: "That's a great choice! We found [X] products for you."
2. Introduce the Match: "But why stop there? Let's turn that [item] into a complete, ready-to-wear look."
3. Present the Look: Describe the complete outfit, highlighting WHY pieces match
4. Use clear formatting with bullet points or bold text
5. Include explanations for each match type
6. End with a call-to-action

IMPORTANT (but keep it natural!): 
- If products were found above, get excited and share them with their product IDs - react like you just found something amazing!
- Then transition to Fashion Match Stylist mode and suggest complementary items
- If NO products were found (especially for specific requests), be honest and friendly about it - like "Aw, we don't have those in stock right now, but let me know if you want me to look for something similar!"

Remember: Be EXCITED, be REAL, be HELPFUL! Show genuine enthusiasm when you find cool stuff!"""
        
        # CRITICAL: Create a backup copy of products BEFORE Bedrock call
        # This ensures we never lose the products even if something goes wrong
        vector_products_backup = list(vector_products) if vector_products else []
        vector_product_ids_backup = list(vector_product_ids) if vector_product_ids else []
        
        products_count_before = len(vector_products)
        product_ids_count_before = len(vector_product_ids)
        print(f"BEFORE Bedrock - vector_products: {products_count_before}, vector_product_ids: {product_ids_count_before}")
        if products_count_before > 0:
            print(f"BEFORE Bedrock - First product ID: {vector_products[0].get('id') if isinstance(vector_products[0], dict) else getattr(vector_products[0], 'id', 'N/A')}")
        
        # Call Bedrock
        response = call_bedrock(full_prompt, system_prompt)
        
        # CRITICAL: Restore products from backup if they were lost
        if len(vector_products) == 0 and len(vector_products_backup) > 0:
            print(f"WARNING: vector_products was lost! Restoring from backup ({len(vector_products_backup)} products)")
            vector_products = vector_products_backup
        if len(vector_product_ids) == 0 and len(vector_product_ids_backup) > 0:
            print(f"WARNING: vector_product_ids was lost! Restoring from backup ({len(vector_product_ids_backup)} IDs)")
            vector_product_ids = vector_product_ids_backup
        
        # Verify products are still there after Bedrock call
        products_count_after = len(vector_products)
        product_ids_count_after = len(vector_product_ids)
        print(f"AFTER Bedrock - vector_products: {products_count_after}, vector_product_ids: {product_ids_count_after}")
        
        # Extract product IDs - use all vector_product_ids (up to 10) to ensure frontend gets them
        # If vector_product_ids is empty but we have vector_products, extract IDs from products
        if vector_product_ids:
            suggested_product_ids = vector_product_ids[:10]
            print(f"Using vector_product_ids: {suggested_product_ids}")
        elif vector_products:
            # Extract IDs from products if vector_product_ids is not available
            suggested_product_ids = []
            print(f"Extracting IDs from {len(vector_products)} vector_products...")
            for p in vector_products[:10]:
                if p:
                    if isinstance(p, dict):
                        pid = p.get('id')
                    else:
                        pid = getattr(p, 'id', None)
                    if pid is not None and pid not in suggested_product_ids:
                        suggested_product_ids.append(int(pid))
            print(f"Extracted {len(suggested_product_ids)} IDs: {suggested_product_ids}")
        else:
            suggested_product_ids = []
            print("WARNING: No vector_product_ids and no vector_products!")
        
        # Final fallback: if we still have products but no IDs, extract from vector_products again
        if not suggested_product_ids and vector_products:
            suggested_product_ids = [int(p.get('id') if isinstance(p, dict) else getattr(p, 'id', None)) 
                                    for p in vector_products[:10] 
                                    if p and (p.get('id') if isinstance(p, dict) else getattr(p, 'id', None))]
            suggested_product_ids = [pid for pid in suggested_product_ids if pid is not None]
        
        # Always set action to 'search_results' if we have products to ensure frontend shows them
        # This ensures the grid updates when products are found
        if len(vector_products) > 0 and action is None:
            action = 'search_results'
        
        # Update response to include navigation message when products are found
        final_response = response['content']
        if action == 'search_results' and len(vector_products) > 0:
            # Don't modify response if user explicitly asked to see in chat
            # The frontend will handle that case
            pass
        
        # Ensure action is always set when products are found
        if len(vector_products) > 0 and not action:
            action = 'search_results'
        
        # Debug logging (only in development)
        if Config.DEBUG:
            print(f"AI Agent Response - vector_products: {len(vector_products)}, suggested_product_ids: {suggested_product_ids}, action: {action}")
            if suggested_product_ids:
                print(f"Product IDs: {suggested_product_ids[:5]}")
        
        # CRITICAL: Always ensure action is set when products are found
        if len(vector_products) > 0 and not action:
            action = 'search_results'
        
        # CRITICAL: Always ensure product IDs are returned when products exist
        if len(vector_products) > 0 and not suggested_product_ids:
            # Extract IDs from products as final fallback
            for p in vector_products[:10]:
                if isinstance(p, dict):
                    pid = p.get('id')
                else:
                    pid = getattr(p, 'id', None)
                if pid is not None and pid not in suggested_product_ids:
                    suggested_product_ids.append(int(pid))
        
        # Final check: ensure action is set when products are found
        final_action = action
        if len(vector_products) > 0 and not final_action:
            final_action = 'search_results'
        
        # CRITICAL: Always ensure we have product IDs if we have products
        if len(vector_products) > 0 and len(suggested_product_ids) == 0:
            print(f"WARNING: Have {len(vector_products)} products but no IDs! Extracting from products...")
            for p in vector_products[:10]:
                if isinstance(p, dict):
                    pid = p.get('id')
                else:
                    pid = getattr(p, 'id', None)
                if pid is not None and int(pid) not in suggested_product_ids:
                    suggested_product_ids.append(int(pid))
            print(f"Extracted {len(suggested_product_ids)} IDs: {suggested_product_ids}")
        
        # Debug: Always log the final response
        print(f"FINAL RESPONSE - vector_products: {len(vector_products)}, suggested_product_ids: {len(suggested_product_ids)}, action: {final_action}")
        if len(vector_products) > 0:
            print(f"First product sample: {vector_products[0] if vector_products else 'None'}")
            print(f"First product ID: {vector_products[0].get('id') if isinstance(vector_products[0], dict) else getattr(vector_products[0], 'id', 'N/A')}")
        else:
            print("WARNING: vector_products is EMPTY in final response!")
        
        # CRITICAL: Use backup if main arrays are empty (final safety net)
        # BUT: Don't use backup if we had strict filters and found nothing (that's intentional)
        if len(vector_products) == 0 and len(vector_products_backup) > 0 and not no_results_detected:
            print(f"FINAL SAFETY: Using backup products ({len(vector_products_backup)} products)")
            vector_products = vector_products_backup
            # Re-extract IDs from backup
            if len(suggested_product_ids) == 0:
                suggested_product_ids = [p.get('id') if isinstance(p, dict) else getattr(p, 'id', None) 
                                       for p in vector_products[:10] 
                                       if p and (p.get('id') if isinstance(p, dict) else getattr(p, 'id', None))]
                suggested_product_ids = [int(pid) for pid in suggested_product_ids if pid is not None]
                print(f"FINAL SAFETY: Extracted {len(suggested_product_ids)} IDs from backup: {suggested_product_ids}")
        
        # CRITICAL: If no results detected with strict filters, don't return products or action
        # This ensures frontend shows chat message instead of navigating to empty grid
        if no_results_detected:
            print("NO RESULTS: Returning empty products array and no action to show chat message")
            products_to_return = []
            ids_to_return = []
            action_to_return = None  # No action = stay in chat, don't navigate
        else:
            # CRITICAL: Ensure we return products even if extraction failed
            products_to_return = vector_products[:10] if len(vector_products) > 0 else []
            ids_to_return = suggested_product_ids if len(suggested_product_ids) > 0 else (vector_product_ids_backup[:10] if len(vector_product_ids_backup) > 0 else [])
            action_to_return = final_action if final_action else ('search_results' if len(vector_products) > 0 else None)
        
        print(f"RETURNING - products: {len(products_to_return)}, ids: {len(ids_to_return)}, action: {action_to_return}")
        if len(products_to_return) > 0:
            first_prod = products_to_return[0]
            first_id = first_prod.get('id') if isinstance(first_prod, dict) else getattr(first_prod, 'id', 'N/A')
            print(f"RETURNING - First product ID: {first_id}")
        if len(ids_to_return) > 0:
            print(f"RETURNING - First ID in array: {ids_to_return[0]}")
        
        # Add fashion match suggestions if products were found
        # This now uses both fashion match rules AND database product relations
        fashion_match_suggestions = None
        if len(products_to_return) > 0:
            primary_product = products_to_return[0]
            primary_name = primary_product.get('name', '')
            primary_id = primary_product.get('id', '')
            
            matched_products = []
            
            # First, try to get related products from database relations
            try:
                from models.product_relation import ProductRelation
                # Ensure relations exist for this product
                product_obj = Product.query.get(primary_id)
                if product_obj:
                    ensure_product_relations(primary_id, product_obj.clothing_type)
                    
                    # Get related products from database
                    relations = ProductRelation.query.filter_by(
                        product_id=primary_id,
                        is_fashion_match=True
                    ).limit(4).all()
                    
                    for relation in relations:
                        if relation.related_product and relation.related_product.is_active:
                            matched_products.append({
                                'product': relation.related_product.to_dict(),
                                'match_type': 'Database Relation',
                                'priority': 1,
                                'explanation': 'Complements this item based on product relations'
                            })
            except Exception as e:
                print(f"Error getting product relations: {e}")
            
            # Also use fashion match rules as fallback/enhancement
            fashion_matches = find_matching_products(primary_name, primary_id)
            
            if fashion_matches and len(matched_products) < 4:
                # Try to find actual products in database that match the suggestions
                for match in fashion_matches[:4]:  # Top 4 matches
                    if len(matched_products) >= 4:
                        break
                    
                    matched_name = match['matched_product']
                    # Search for products that match the suggested item name
                    matched_product_query = Product.query.filter(
                        or_(
                            Product.name.ilike(f'%{matched_name.split("/")[0]}%'),  # Take first part before /
                            Product.name.ilike(f'%{matched_name.split()[0]}%')  # Take first word
                        )
                    ).filter_by(is_active=True).limit(1).first()
                    
                    if matched_product_query:
                        # Check if already added
                        if not any(mp['product']['id'] == matched_product_query.id for mp in matched_products):
                            matched_products.append({
                                'product': matched_product_query.to_dict(),
                                'match_type': match['match_type'],
                                'priority': match['priority'],
                                'explanation': get_match_explanation(match['match_type'])
                            })
            
            if matched_products:
                fashion_match_suggestions = {
                    'primary_product': {
                        'id': primary_id,
                        'name': primary_name
                    },
                    'matches': matched_products[:4]  # Limit to 4 matches
                }
        
        return jsonify({
            'response': final_response,
            'suggested_products': products_to_return,  # Return up to 10 products
            'suggested_product_ids': ids_to_return,  # Return all IDs (already limited to 10)
            'action': action_to_return,  # Always set action when products found
            'fashion_match_suggestions': fashion_match_suggestions  # Fashion Match Stylist suggestions
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/search', methods=['POST'])
def ai_search():
    """AI-powered product search."""
    try:
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        # Use vector search
        product_ids = search_products_vector(query, n_results=20)
        
        if product_ids:
            products = Product.query.filter(Product.id.in_(product_ids)).all()
            products_dict = {p.id: p.to_dict() for p in products}
            # Maintain order from vector search
            ordered_products = [products_dict[pid] for pid in product_ids if pid in products_dict]
        else:
            # Fallback to regular search
            products = Product.query.filter(
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%')
                )
            ).filter_by(is_active=True).limit(20).all()
            ordered_products = [p.to_dict() for p in products]
        
        return jsonify({
            'products': ordered_products,
            'count': len(ordered_products)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/filter', methods=['POST'])
def ai_filter():
    """AI-powered product filtering."""
    try:
        data = request.get_json()
        criteria = data.get('criteria', {})
        
        products = search_products_by_criteria(criteria)
        
        return jsonify({
            'products': products,
            'count': len(products)
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/compare', methods=['POST'])
def compare_products():
    """Compare multiple products."""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        
        if not product_ids or len(product_ids) < 2:
            return jsonify({'error': 'At least 2 product IDs are required'}), 400
        
        products = Product.query.filter(Product.id.in_(product_ids)).filter_by(is_active=True).all()
        
        if len(products) != len(product_ids):
            return jsonify({'error': 'Some products not found'}), 404
        
        # Convert to dict while session is active
        products_dict = [p.to_dict() for p in products]
        
        return jsonify({
            'products': products_dict,
            'comparison': {
                'price_range': {
                    'min': float(min(p.price for p in products)),
                    'max': float(max(p.price for p in products))
                },
                'categories': list(set(p.category for p in products)),
                'colors': list(set(p.color for p in products if p.color))
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@ai_agent_bp.route('/summarize', methods=['POST'])
def summarize_text():
    """Summarize text for text-to-speech when it's too long."""
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        print(f"[SUMMARIZE] Summarizing text ({len(text)} characters)")
        
        # Create a summarization prompt
        summarize_prompt = f"""Please summarize the following text in a concise, natural way that's perfect for speaking aloud. 
Keep the key information and main points, but make it shorter and more conversational. 
Aim for about 50-80 words. Keep the friendly, excited tone if present.

Text to summarize:
{text}

Summary:"""
        
        # Use a simpler system prompt for summarization
        system_prompt = """You are a helpful assistant that creates concise, natural summaries perfect for text-to-speech. 
Keep summaries conversational and maintain the original tone and key information."""
        
        # Call Bedrock for summarization
        result = call_bedrock(summarize_prompt, system_prompt)
        summary = result.get('content', text)  # Fallback to original if summarization fails
        
        print(f"[SUMMARIZE] Summary created ({len(summary)} characters)")
        
        return jsonify({
            'summary': summary,
            'original_length': len(text),
            'summary_length': len(summary)
        })
        
    except Exception as e:
        print(f"[SUMMARIZE] Error: {str(e)}")
        # Return original text if summarization fails
        return jsonify({
            'summary': text,
            'original_length': len(text),
            'summary_length': len(text),
            'error': str(e)
        }), 200  # Return 200 so frontend can still use the original text

@ai_agent_bp.route('/text-to-speech/status', methods=['GET'])
def tts_status():
    """Check if AWS Polly is available and configured."""
    try:
        # Safely get Config values with defaults
        aws_region = None
        has_credentials = False
        try:
            aws_region = Config.AWS_REGION if hasattr(Config, 'AWS_REGION') and Config.AWS_REGION else None
            has_credentials = bool(
                hasattr(Config, 'AWS_ACCESS_KEY_ID') and Config.AWS_ACCESS_KEY_ID and
                hasattr(Config, 'AWS_SECRET_ACCESS_KEY') and Config.AWS_SECRET_ACCESS_KEY
            )
        except Exception as config_error:
            print(f"Warning: Error accessing Config: {config_error}")
        
        # Check if AWS CLI credentials are available (default credential chain)
        has_aws_cli_credentials = False
        if not has_credentials:
            try:
                # Try to get credentials from default chain
                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials:
                    has_aws_cli_credentials = True
            except:
                pass
        
        status = {
            'available': polly_available,
            'client_initialized': polly_client is not None,
            'aws_region': aws_region,
            'has_credentials': has_credentials,
            'has_aws_cli_credentials': has_aws_cli_credentials
        }
        
        if polly_client and polly_available:
            try:
                # Test by getting available voices (limit to first 5 for response size)
                voices_response = polly_client.describe_voices(LanguageCode='en-US')
                voices_list = voices_response.get('Voices', [])[:5]  # Limit to first 5
                status['test_successful'] = True
                status['available_voices'] = [v['Id'] for v in voices_list]
            except Exception as e:
                status['test_successful'] = False
                status['test_error'] = str(e)
        
        return jsonify(status), 200
    except Exception as e:
        print(f"Error in tts_status: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'available': False}), 500

@ai_agent_bp.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech using AWS Polly with natural, excited voices."""
    import re
    import html
    import base64
    import traceback
    
    print("=" * 80)
    print("[AWS POLLY] Text-to-Speech Request Received")
    print("=" * 80)
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        voice_gender = data.get('voice_gender', 'woman')  # 'woman' or 'man'
        
        print(f"[AWS POLLY] Request Details:")
        print(f"  - Text length: {len(text)} characters")
        print(f"  - Voice gender: {voice_gender}")
        print(f"  - Text preview: {text[:100]}..." if len(text) > 100 else f"  - Text: {text}")
        
        if not text:
            print("[AWS POLLY] ❌ ERROR: No text provided")
            return jsonify({'error': 'Text is required'}), 400
        
        print(f"[AWS POLLY] Checking Polly availability...")
        print(f"  - polly_client exists: {polly_client is not None}")
        print(f"  - polly_available: {polly_available}")
        print(f"  - AWS_ACCESS_KEY_ID configured: {bool(Config.AWS_ACCESS_KEY_ID)}")
        print(f"  - AWS_SECRET_ACCESS_KEY configured: {bool(Config.AWS_SECRET_ACCESS_KEY)}")
        print(f"  - AWS_REGION: {Config.AWS_REGION}")
        
        if not polly_client or not polly_available:
            error_msg = 'Polly client not available. '
            if not Config.AWS_ACCESS_KEY_ID or not Config.AWS_SECRET_ACCESS_KEY:
                error_msg += 'Please configure AWS credentials via .env file (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) or AWS CLI (aws configure).'
            else:
                error_msg += 'Please check your AWS credentials and Polly permissions.'
            print(f"[AWS POLLY] ❌ ERROR: {error_msg}")
            # Return 503 Service Unavailable instead of 500 for missing service
            return jsonify({'error': error_msg, 'service_unavailable': True}), 503
        
        print("[AWS POLLY] ✅ Polly client is available, proceeding with text processing...")
        
        # Clean text for better speech
        clean_text = text
        original_length = len(clean_text)
        
        # Remove product IDs but keep context
        clean_text = re.sub(r'Product\s*#\d+', '', clean_text, flags=re.IGNORECASE)
        # Remove URLs
        clean_text = re.sub(r'https?://[^\s]+', '', clean_text)
        # Remove markdown
        clean_text = clean_text.replace('*', '').replace('_', '').replace('`', '')
        # Remove emojis and special characters (keep basic punctuation)
        clean_text = re.sub(r"[^\w\s.,!?;:()\-'\"]", ' ', clean_text)
        # Clean up spacing
        clean_text = ' '.join(clean_text.split())
        
        print(f"[AWS POLLY] Text cleaning:")
        print(f"  - Original length: {original_length} characters")
        print(f"  - Cleaned length: {len(clean_text)} characters")
        print(f"  - Cleaned text preview: {clean_text[:100]}..." if len(clean_text) > 100 else f"  - Cleaned text: {clean_text}")
        
        if not clean_text:
            print("[AWS POLLY] ❌ ERROR: No valid text after cleaning")
            return jsonify({'error': 'No valid text to convert'}), 400
        
        # Select voice based on gender preference
        # Using attractive, warm American voices with appealing tone
        if voice_gender == 'woman':
            # Kendra - warm, friendly, attractive American voice (very appealing)
            # Alternative: Amy (expressive), Kimberly (smooth), Salli (clear, warm)
            voice_id = 'Kendra'  # Warm, attractive, American accent
        else:
            # Joey - young, energetic, attractive American male voice
            # Alternative: Justin (expressive), Matthew (calm, professional)
            voice_id = 'Joey'  # Attractive, energetic American accent
        
        print(f"[AWS POLLY] Voice selection: {voice_id} (gender: {voice_gender})")
        
        # Use standard engine with SSML for better control over prosody
        # Standard engine supports prosody tags (rate, pitch, volume) for better expression
        import re
        import html
        
        # Escape HTML/XML special characters for SSML
        escaped_text = html.escape(clean_text)
        
        # Detect excitement level in text
        excitement_indicators = ['!', 'OMG', 'wow', 'awesome', 'amazing', 'great', 'perfect', 
                                 'love', 'fantastic', 'excellent', 'wonderful', 'beautiful']
        excitement_level = sum(1 for indicator in excitement_indicators if indicator.lower() in text.lower())
        has_exclamation = '!' in text
        
        # Create SSML with prosody for attractive, warm, appealing American voice
        # Rate: slower for more appealing, seductive feel (82-85% = slower, more alluring)
        # Pitch: slightly lower for warmer, more attractive tone (-1% to +1%)
        # Volume: medium for clear but intimate feel
        # Phonation: soft for appealing, warm, attractive tone
        
        if excitement_level > 2 or has_exclamation:
            # More excited: slightly faster but still appealing, warmer pitch
            ssml_text = f'<speak><prosody rate="85%" pitch="+1%" volume="medium">' \
                       f'<amazon:effect phonation="soft">{escaped_text}</amazon:effect>' \
                       f'</prosody></speak>'
            print("[AWS POLLY] Using excited appealing SSML (rate: 85%, pitch: +1%, soft phonation)")
        else:
            # Normal: slower, warmer, more attractive and appealing tone
            ssml_text = f'<speak><prosody rate="82%" pitch="-1%" volume="medium">' \
                       f'<amazon:effect phonation="soft">{escaped_text}</amazon:effect>' \
                       f'</prosody></speak>'
            print("[AWS POLLY] Using warm appealing SSML (rate: 82%, pitch: -1%, soft phonation)")
        
        print(f"[AWS POLLY] SSML length: {len(ssml_text)} characters")
        print(f"[AWS POLLY] Text preview: {clean_text[:200]}..." if len(clean_text) > 200 else f"[AWS POLLY] Text: {clean_text}")
        
        # Use standard engine with SSML for better prosody control
        import time
        start_time = time.time()
        response = None
        engine_used = 'standard'
        
        try:
            print(f"[AWS POLLY] Calling AWS Polly with standard engine and SSML...")
            print(f"  - VoiceId: {voice_id}")
            print(f"  - Engine: standard (supports SSML prosody)")
            print(f"  - OutputFormat: mp3")
            print(f"  - TextType: ssml")
            
            response = polly_client.synthesize_speech(
                Text=ssml_text,
                OutputFormat='mp3',
                VoiceId=voice_id,
                TextType='ssml'  # Using SSML for prosody control
                # Standard engine (no Engine parameter = standard)
            )
            elapsed_time = time.time() - start_time
            print(f"[AWS POLLY] ✅ Polly API call successful with standard engine + SSML (took {elapsed_time:.2f}s)")
        except Exception as ssml_error:
            elapsed_time = time.time() - start_time
            error_msg = str(ssml_error)
            print(f"[AWS POLLY] ⚠️ SSML failed, trying plain text with standard engine...")
            print(f"[AWS POLLY] Error: {error_msg}")
            
            # Fallback: plain text without SSML
            try:
                start_time = time.time()
                response = polly_client.synthesize_speech(
                    Text=clean_text,
                    OutputFormat='mp3',
                    VoiceId=voice_id
                    # Standard engine with plain text
                )
                elapsed_time = time.time() - start_time
                print(f"[AWS POLLY] ✅ Polly API call successful with standard engine + plain text (took {elapsed_time:.2f}s)")
            except Exception as plain_error:
                elapsed_time = time.time() - start_time
                print(f"[AWS POLLY] ❌ ERROR: Both SSML and plain text failed after {elapsed_time:.2f}s")
                print(f"[AWS POLLY] Error type: {type(plain_error).__name__}")
                print(f"[AWS POLLY] Error message: {str(plain_error)}")
                print(f"[AWS POLLY] Error traceback:")
                traceback.print_exc()
                raise
        
        # Get audio stream
        print("[AWS POLLY] Reading audio stream from response...")
        audio_stream = response['AudioStream'].read()
        audio_size = len(audio_stream)
        print(f"[AWS POLLY] ✅ Audio stream received: {audio_size} bytes ({audio_size / 1024:.2f} KB)")
        
        # Return as base64 encoded audio
        print("[AWS POLLY] Encoding audio to base64...")
        audio_base64 = base64.b64encode(audio_stream).decode('utf-8')
        base64_size = len(audio_base64)
        print(f"[AWS POLLY] ✅ Base64 encoding complete: {base64_size} characters")
        
        print("[AWS POLLY] ✅ SUCCESS: Returning audio response to client")
        print("=" * 80)
        
        return jsonify({
            'audio': audio_base64,
            'format': 'mp3',
            'voice': voice_id,
            'engine': engine_used
        })
        
    except Exception as e:
        print(f"[AWS POLLY] ❌ EXCEPTION in text-to-speech endpoint")
        print(f"[AWS POLLY] Error type: {type(e).__name__}")
        print(f"[AWS POLLY] Error message: {str(e)}")
        print(f"[AWS POLLY] Full traceback:")
        traceback.print_exc()
        print("=" * 80)
        return jsonify({'error': f'Failed to generate speech: {str(e)}'}), 500

@ai_agent_bp.route('/upload-image', methods=['POST'])
def upload_image():
    """Handle image upload for AI agent to analyze fashion items and find similar products."""
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Check file type
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'error': f'Invalid file type. Allowed: {", ".join(allowed_extensions)}'}), 400
        
        # Read image data
        from PIL import Image
        import io
        import base64
        import re
        
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        # Validate image size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'error': 'Image too large. Maximum size is 10MB'}), 400
        
        # Resize if too large (max 2000x2000)
        max_dimension = 2000
        if image.size[0] > max_dimension or image.size[1] > max_dimension:
            image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        
        # Convert to base64 for storage/transmission
        buffered = io.BytesIO()
        # Save as JPEG for smaller size
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')
        
        image.save(buffered, format='JPEG', quality=85)
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        # Analyze image with AI and extract metadata
        analysis_prompt = """Analyze this fashion image and provide a structured response in the following format:

ITEM_TYPE: [e.g., dress, shirt, t-shirt, pants, jeans, blouse, etc.]
COLOR: [primary color, e.g., blue, red, black, white, etc.]
CATEGORY: [men, women, or kids]
CLOTHING_TYPE: [specific type like "T-Shirt", "Dress", "Jeans", etc.]
STYLE_FEATURES: [e.g., v-neck, long sleeve, casual, formal, etc.]
OCCASION: [e.g., casual, business, date night, etc.]
FABRIC: [if visible, e.g., cotton, denim, etc.]

Then provide a natural, enthusiastic description of the item in 2-3 sentences, highlighting its key features and style."""
        
        # Analyze image using Bedrock (or fallback)
        metadata = {}
        analysis_text = ""
        similar_products = []
        
        if bedrock_runtime:
            # Use Bedrock to analyze the image
            # Note: For Claude 3.5 Sonnet with image support, you would use:
            # body = {
            #     "anthropic_version": "bedrock-2023-05-31",
            #     "max_tokens": 1024,
            #     "messages": [{
            #         "role": "user",
            #         "content": [
            #             {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
            #             {"type": "text", "text": analysis_prompt}
            #         ]
            #     }]
            # }
            
            # For now, use text-based analysis with a prompt asking user to describe
            response = call_bedrock(
                "Please analyze this fashion image. " + analysis_prompt,
                system_prompt="You are a fashion expert analyzing clothing items from images. Provide detailed, structured analysis."
            )
            analysis_text = response.get('content', '')
            
            # Extract metadata from analysis
            if analysis_text:
                # Extract ITEM_TYPE or CLOTHING_TYPE
                item_match = re.search(r'(?:ITEM_TYPE|CLOTHING_TYPE):\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if item_match:
                    clothing_type = item_match.group(1).strip()
                    # Normalize common clothing types
                    clothing_type_lower = clothing_type.lower()
                    if 'dress' in clothing_type_lower:
                        metadata['clothing_type'] = 'Dress'
                    elif 'shirt' in clothing_type_lower or 'blouse' in clothing_type_lower:
                        metadata['clothing_type'] = 'Shirt' if 't-shirt' not in clothing_type_lower else 'T-Shirt'
                    elif 't-shirt' in clothing_type_lower or 'tshirt' in clothing_type_lower:
                        metadata['clothing_type'] = 'T-Shirt'
                    elif 'pants' in clothing_type_lower or 'trousers' in clothing_type_lower:
                        metadata['clothing_type'] = 'Pants'
                    elif 'jeans' in clothing_type_lower:
                        metadata['clothing_type'] = 'Jeans'
                    elif 'polo' in clothing_type_lower:
                        metadata['clothing_type'] = 'Polo Shirt'
                    else:
                        metadata['clothing_type'] = clothing_type
                
                # Extract COLOR
                color_match = re.search(r'COLOR:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if color_match:
                    color = color_match.group(1).strip().lower()
                    # Normalize colors
                    color_map = {
                        'blue': 'Blue', 'navy': 'Navy', 'light blue': 'Blue',
                        'red': 'Red', 'maroon': 'Maroon', 'burgundy': 'Red',
                        'black': 'Black', 'dark': 'Black',
                        'white': 'White', 'cream': 'White', 'ivory': 'White',
                        'green': 'Green', 'emerald': 'Green',
                        'yellow': 'Yellow', 'gold': 'Yellow',
                        'pink': 'Pink', 'rose': 'Pink',
                        'purple': 'Purple', 'violet': 'Purple',
                        'gray': 'Gray', 'grey': 'Gray', 'silver': 'Gray',
                        'brown': 'Brown', 'tan': 'Brown', 'beige': 'Beige',
                        'orange': 'Orange'
                    }
                    for key, value in color_map.items():
                        if key in color:
                            metadata['color'] = value
                            break
                    if 'color' not in metadata:
                        metadata['color'] = color_match.group(1).strip()
                
                # Extract CATEGORY
                category_match = re.search(r'CATEGORY:\s*(men|women|kids)', analysis_text, re.IGNORECASE)
                if category_match:
                    metadata['category'] = category_match.group(1).lower()
                else:
                    # Try to infer from text
                    text_lower = analysis_text.lower()
                    if any(word in text_lower for word in ['women', 'woman', 'ladies', 'female']):
                        metadata['category'] = 'women'
                    elif any(word in text_lower for word in ['men', 'man', 'male', 'gentleman']):
                        metadata['category'] = 'men'
                    elif any(word in text_lower for word in ['kids', 'kid', 'children', 'child']):
                        metadata['category'] = 'kids'
                
                # Extract OCCASION
                occasion_match = re.search(r'OCCASION:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if occasion_match:
                    occasion = occasion_match.group(1).strip().lower()
                    # Normalize occasions
                    if 'casual' in occasion:
                        metadata['occasion'] = 'casual'
                    elif 'business' in occasion or 'professional' in occasion or 'formal' in occasion:
                        metadata['occasion'] = 'business_formal' if 'formal' in occasion else 'business_casual'
                    elif 'date' in occasion or 'night' in occasion:
                        metadata['occasion'] = 'date_night'
                    elif 'wedding' in occasion:
                        metadata['occasion'] = 'wedding'
                    else:
                        metadata['occasion'] = occasion
                
                # Extract FABRIC
                fabric_match = re.search(r'FABRIC:\s*([^\n]+)', analysis_text, re.IGNORECASE)
                if fabric_match:
                    fabric = fabric_match.group(1).strip()
                    # Normalize fabrics
                    fabric_lower = fabric.lower()
                    if 'cotton' in fabric_lower:
                        metadata['fabric'] = 'Cotton'
                    elif 'polyester' in fabric_lower:
                        metadata['fabric'] = 'Polyester'
                    elif 'wool' in fabric_lower:
                        metadata['fabric'] = 'Wool'
                    elif 'silk' in fabric_lower:
                        metadata['fabric'] = 'Silk'
                    elif 'denim' in fabric_lower:
                        metadata['fabric'] = 'Denim'
                    elif 'linen' in fabric_lower:
                        metadata['fabric'] = 'Linen'
                    else:
                        metadata['fabric'] = fabric
                
                # Extract the natural description (text after the structured data)
                # Remove structured metadata lines
                lines = analysis_text.split('\n')
                desc_lines = []
                skip_next = False
                for i, line in enumerate(lines):
                    line_stripped = line.strip()
                    if any(line_stripped.startswith(prefix) for prefix in ['ITEM_TYPE:', 'COLOR:', 'CATEGORY:', 'CLOTHING_TYPE:', 'STYLE_FEATURES:', 'OCCASION:', 'FABRIC:']):
                        skip_next = True
                        continue
                    if skip_next and not line_stripped:
                        skip_next = False
                        continue
                    if not skip_next and line_stripped:
                        desc_lines.append(line)
                
                if desc_lines:
                    analysis_text = '\n'.join(desc_lines).strip()
                elif not any(line.strip().startswith(('ITEM_TYPE:', 'COLOR:', 'CATEGORY:')) for line in lines):
                    # If no structured format, use the whole text
                    analysis_text = analysis_text.strip()
        else:
            # Fallback message
            analysis_text = "I can see you've uploaded an image! To get detailed fashion analysis, AWS Bedrock needs to be configured."
            metadata = {}
        
        # Search for similar products based on extracted metadata
        search_criteria = {}
        if metadata.get('category'):
            search_criteria['category'] = metadata['category']
        if metadata.get('color'):
            search_criteria['color'] = metadata['color']
        if metadata.get('clothing_type'):
            search_criteria['clothing_type'] = metadata['clothing_type']
        if metadata.get('occasion'):
            search_criteria['occasion'] = metadata['occasion']
        if metadata.get('fabric'):
            search_criteria['fabric'] = metadata['fabric']
        
        # Search products using criteria
        similar_products = []
        if search_criteria:
            # Try exact match first
            similar_products = search_products_by_criteria(search_criteria)
            
            # If not enough results, try partial matches
            if len(similar_products) < 5:
                # Try without occasion (less strict)
                partial_criteria = {k: v for k, v in search_criteria.items() if k != 'occasion'}
                if partial_criteria and len(partial_criteria) < len(search_criteria):
                    partial_products = search_products_by_criteria(partial_criteria)
                    # Add products not already in similar_products
                    existing_ids = {p['id'] for p in similar_products}
                    for p in partial_products:
                        if p['id'] not in existing_ids:
                            similar_products.append(p)
            
            # If still not enough, try just category and color
            if len(similar_products) < 5 and search_criteria.get('category') and search_criteria.get('color'):
                simple_criteria = {
                    'category': search_criteria['category'],
                    'color': search_criteria['color']
                }
                simple_products = search_products_by_criteria(simple_criteria)
                existing_ids = {p['id'] for p in similar_products}
                for p in simple_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
            
            # If still not enough, try just category
            if len(similar_products) < 5 and search_criteria.get('category'):
                category_only = {'category': search_criteria['category']}
                category_products = search_products_by_criteria(category_only)
                existing_ids = {p['id'] for p in similar_products}
                for p in category_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
        
        # Fallback: use vector search with description
        if len(similar_products) < 3 and analysis_text:
            # Create search query from analysis
            search_terms = []
            if metadata.get('clothing_type'):
                search_terms.append(metadata['clothing_type'])
            if metadata.get('color'):
                search_terms.append(metadata['color'])
            if metadata.get('category'):
                search_terms.append(metadata['category'])
            
            search_query = ' '.join(search_terms) if search_terms else analysis_text[:200]
            vector_product_ids = search_products_vector(search_query, n_results=10)
            if vector_product_ids:
                products = Product.query.filter(Product.id.in_(vector_product_ids)).filter_by(is_active=True).all()
                vector_products = [p.to_dict() for p in products]
                # Add products not already found
                existing_ids = {p['id'] for p in similar_products}
                for p in vector_products:
                    if p['id'] not in existing_ids:
                        similar_products.append(p)
        
        # Limit to 8 products for display
        similar_products = similar_products[:8]
        
        # Format metadata into a nice sentence
        metadata_sentence = ""
        if metadata:
            parts = []
            if metadata.get('clothing_type'):
                parts.append(f"a {metadata['clothing_type']}")
            if metadata.get('color'):
                parts.append(f"in {metadata['color']}")
            if metadata.get('category'):
                parts.append(f"for {metadata['category']}")
            if metadata.get('occasion'):
                parts.append(f"suitable for {metadata['occasion']}")
            
            if parts:
                metadata_sentence = "This appears to be " + " ".join(parts) + "."
            else:
                metadata_sentence = "I've analyzed your image and found some similar items!"
        else:
            metadata_sentence = "I've analyzed your image and found some similar items!"
        
        # Combine analysis and metadata into a natural response
        if analysis_text and analysis_text != "I can see you've uploaded an image! To get detailed fashion analysis, AWS Bedrock needs to be configured.":
            full_response = f"{metadata_sentence}\n\n{analysis_text}"
        else:
            full_response = metadata_sentence
        
        if similar_products:
            full_response += f"\n\nI found {len(similar_products)} similar product{'s' if len(similar_products) != 1 else ''} in our store that you might like!"
        
        return jsonify({
            'success': True,
            'message': full_response,
            'image_data': image_base64,
            'image_format': 'jpeg',
            'metadata': metadata,
            'metadata_sentence': metadata_sentence,
            'similar_products': similar_products,
            'similar_product_ids': [p['id'] for p in similar_products]
        })
        
    except Exception as e:
        print(f"Error uploading image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to process image: {str(e)}'}), 500

@ai_agent_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze uploaded image using AI to provide fashion recommendations."""
    try:
        data = request.get_json()
        image_base64 = data.get('image_data', '')
        user_query = data.get('query', 'What is this item and what would match it?')
        
        if not image_base64:
            return jsonify({'error': 'No image data provided'}), 400
        
        # Decode base64 image
        import base64
        import io
        from PIL import Image
        
        try:
            image_bytes = base64.b64decode(image_base64)
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            return jsonify({'error': f'Invalid image data: {str(e)}'}), 400
        
        # Build prompt for AI analysis
        # Note: Claude 3.5 Sonnet in Bedrock supports image inputs via base64
        # For now, we'll use text-based analysis
        analysis_prompt = f"""You are a fashion expert analyzing a clothing item from an uploaded image.

User's question: {user_query}

Based on the image provided, please:
1. Identify the type of clothing (dress, shirt, pants, etc.)
2. Describe the color(s) and style
3. Suggest matching items or complementary pieces
4. Recommend occasions where this would be appropriate
5. Provide styling tips

Be enthusiastic and helpful, matching the tone of our shopping assistant!"""
        
        # Call Bedrock with the analysis
        if bedrock_runtime:
            # For Claude 3.5 Sonnet with image support, you would use:
            # body = {
            #     "anthropic_version": "bedrock-2023-05-31",
            #     "max_tokens": 1024,
            #     "messages": [{
            #         "role": "user",
            #         "content": [
            #             {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
            #             {"type": "text", "text": analysis_prompt}
            #         ]
            #     }]
            # }
            
            # For now, use text-only analysis
            response = call_bedrock(analysis_prompt, system_prompt="You are a fashion expert helping customers find matching items and styling advice.")
            analysis = response.get('content', 'Unable to analyze image at this time.')
        else:
            analysis = """I can see you've uploaded an image! To get detailed fashion analysis, AWS Bedrock needs to be configured with Claude 3.5 Sonnet (which supports image analysis).

For now, you can describe the item to me and I'll help you find similar products or matching items!"""
        
        # Search for similar products based on the analysis
        # This would be enhanced with actual image recognition/ML in production
        similar_products = []
        
        return jsonify({
            'success': True,
            'analysis': analysis,
            'similar_products': similar_products,
            'suggestion': 'Try asking me to find similar items or suggest matching pieces!'
        })
        
    except Exception as e:
        print(f"Error analyzing image: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Failed to analyze image: {str(e)}'}), 500

