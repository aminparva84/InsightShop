from flask import Blueprint, request, jsonify
from models.database import db
from models.product import Product
from utils.vector_db import search_products_vector
from utils.fashion_kb import get_fashion_knowledge_base_text, get_color_matching_advice, get_fabric_info, get_occasion_advice
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
        bedrock_runtime = boto3.client(
            'bedrock-runtime',
            region_name=Config.AWS_REGION,
            aws_access_key_id=Config.AWS_ACCESS_KEY_ID if Config.AWS_ACCESS_KEY_ID else None,
            aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY if Config.AWS_SECRET_ACCESS_KEY else None
        )
    except Exception as e:
        print(f"Warning: Could not initialize Bedrock client: {e}")

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
            system_prompt = """You are a helpful shopping assistant for an online clothing store. 
            You can help customers find products, compare items, and make recommendations.
            Be friendly, helpful, and concise in your responses."""
        
        # Prepare the message for Claude
        messages = [
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": messages
        }
        
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
        
        # Extract category from message
        detected_category = None
        if 'men' in message or 'man' in message:
            detected_category = 'men'
        elif 'women' in message or 'woman' in message or 'ladies' in message:
            detected_category = 'women'
        elif 'kids' in message or 'kid' in message or 'children' in message:
            detected_category = 'kids'
        
        # Extract color from message early so we can use it in search
        # Use comprehensive color names
        from utils.color_names import normalize_color_name, ALL_COLOR_NAMES
        detected_color = normalize_color_name(message)
        
        # If no match found, try basic keywords as fallback
        if not detected_color:
            color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange', 'navy', 'beige', 'tan']
            for color in color_keywords:
                if color in message:
                    detected_color = color
                    break
        
        # Extract clothing type from message - be more flexible
        detected_clothing_type = None
        clothing_type_keywords = {
            'T-Shirt': ['t-shirt', 'tshirt', 'tee', 't shirt'],
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
        # Check for clothing type - prioritize more specific matches
        for clothing_type, keywords in clothing_type_keywords.items():
            if any(keyword in message for keyword in keywords):
                detected_clothing_type = clothing_type
                break
        
        # If "shirt" is mentioned but no specific type detected, use generic "Shirt"
        if not detected_clothing_type and 'shirt' in message:
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
        
        # Extract color from message for better search
        detected_color = None
        color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange', 'navy', 'beige', 'tan']
        for color in color_keywords:
            if color in message:
                detected_color = color
                break
        
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
                query = query.filter(
                    or_(
                        Product.color.ilike(f'%{detected_color}%'),
                        Product.name.ilike(f'%{detected_color}%')
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
                
                # Extract search terms from message
                if 'women' in message or 'woman' in message or 'ladies' in message:
                    search_query = search_query.filter_by(category='women')
                elif 'men' in message or 'man' in message:
                    search_query = search_query.filter_by(category='men')
                elif 'kids' in message or 'kid' in message or 'children' in message:
                    search_query = search_query.filter_by(category='kids')
                
                # Color search
                color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange']
                detected_color = None
                for color in color_keywords:
                    if color in message:
                        detected_color = color
                        break
                
                if detected_color:
                    search_query = search_query.filter(
                        or_(
                            Product.color.ilike(f'%{detected_color}%'),
                            Product.name.ilike(f'%{detected_color}%')
                        )
                    )
                
                # Clothing type search
                clothing_keywords = ['shirt', 'dress', 'pants', 'jeans', 'shoes', 'jacket', 'sweater', 'blazer', 'suit']
                detected_clothing = None
                for clothing in clothing_keywords:
                    if clothing in message:
                        detected_clothing = clothing
                        break
                
                if detected_clothing:
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
        
        # Build system prompt with product context and fashion knowledge
        system_prompt = f"""You are a knowledgeable, friendly, and conversational fashion shopping assistant for InsightShop, an online clothing store.

FASHION KNOWLEDGE BASE:
{fashion_kb}

PRODUCT DATABASE:
You have access to {len(all_products)} products in the store. Here are some sample products with their details:
{json.dumps(all_products[:20], indent=2)}

IMPORTANT GUIDELINES:
1. When showing products, ALWAYS include the product ID number: "Product #ID: Name - $Price"
2. Be conversational and provide DETAILED information about each product including:
   - Fabric/material composition and its properties
   - Color matching suggestions
   - Style advice and how to wear it
   - Occasion appropriateness
   - Care instructions when relevant
3. When discussing colors, reference the color matching guide from the knowledge base
4. When discussing fabrics, explain their properties, care, and best uses
5. When customers ask about occasions, provide specific styling advice
6. Be enthusiastic but professional - like a knowledgeable friend helping with fashion choices

EXAMPLE RESPONSES:
Instead of: "Here's a blue shirt for $25"
Say: "I found Product #123: Blue T-Shirt for Men - $25.00. This is made from 100% premium cotton, which means it's breathable and perfect for everyday wear. The blue color pairs beautifully with navy, white, gray, and beige - you could wear it with navy chinos for a classic look, or with white jeans for a fresh summer style. It's versatile enough for casual outings, weekend wear, or even a relaxed business casual look when paired with a blazer."

You can help customers:
- Find products by category, color, size, price, or fabric
- Compare products by ID or selected items
- Get styling advice and color matching suggestions
- Learn about fabrics and their properties
- Get occasion-appropriate recommendations
- Answer detailed questions about products

Be friendly, detailed, and helpful. Share your fashion knowledge generously!"""
        
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
        
        full_prompt = f"""Customer message: {message}

Available products in store: {len(all_products)} total products.
{recent_products_text}

Please help the customer with their request. When mentioning products, ALWAYS include the product ID number like "Product #ID: Name - Price".

IMPORTANT: 
- If products were found above, you MUST mention them and their product IDs.
- If NO products were found (especially for specific category/clothing type requests), you MUST tell the customer we don't have those items. Be honest and don't show unrelated products."""
        
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
        
        return jsonify({
            'response': final_response,
            'suggested_products': products_to_return,  # Return up to 10 products
            'suggested_product_ids': ids_to_return,  # Return all IDs (already limited to 10)
            'action': action_to_return  # Always set action when products found
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

