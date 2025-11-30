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
        detected_color = None
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
        
        # Perform enhanced search with filters
        vector_product_ids = []
        vector_products = []
        
        # Extract color from message for better search
        detected_color = None
        color_keywords = ['blue', 'red', 'black', 'white', 'green', 'yellow', 'pink', 'purple', 'gray', 'grey', 'brown', 'orange', 'navy', 'beige', 'tan']
        for color in color_keywords:
            if color in message:
                detected_color = color
                break
        
        # If we have specific filters, use direct database query first
        if detected_occasion or detected_age_group or detected_category or detected_clothing_type or detected_color:
            query = Product.query.filter_by(is_active=True)
            
            if detected_category:
                query = query.filter_by(category=detected_category)
            
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
        if vector_products:
            recent_products_text = f"\nIMPORTANT: I found {len(vector_products)} product(s) matching the customer's request:\n"
            for p in vector_products[:10]:  # Show up to 10 products
                recent_products_text += f"Product #{p['id']}: {p['name']} - ${float(p['price']):.2f} ({p['category']}, {p.get('color', 'N/A')})\n"
            recent_products_text += "\nThese products ARE available in our store. Please show them to the customer and include their product IDs."
        else:
            recent_products_text = "\nNo products found matching the customer's specific criteria. You may suggest similar products or ask for clarification."
        
        full_prompt = f"""Customer message: {message}

Available products in store: {len(all_products)} total products.
{recent_products_text}

Please help the customer with their request. When mentioning products, ALWAYS include the product ID number like "Product #ID: Name - Price".

IMPORTANT: If products were found above, you MUST mention them and their product IDs. Do NOT say we don't have products if they were found in the search results."""
        
        # Call Bedrock
        response = call_bedrock(full_prompt, system_prompt)
        
        # Extract product IDs - use all vector_product_ids (up to 10) to ensure frontend gets them
        # If vector_product_ids is empty but we have vector_products, extract IDs from products
        if vector_product_ids:
            suggested_product_ids = vector_product_ids[:10]
        elif vector_products:
            # Extract IDs from products if vector_product_ids is not available
            suggested_product_ids = []
            for p in vector_products[:10]:
                if p:
                    if isinstance(p, dict):
                        pid = p.get('id')
                    else:
                        pid = getattr(p, 'id', None)
                    if pid is not None and pid not in suggested_product_ids:
                        suggested_product_ids.append(int(pid))
        else:
            suggested_product_ids = []
        
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
        
        # Debug logging
        print(f"AI Agent Response - vector_products: {len(vector_products)}, suggested_product_ids: {suggested_product_ids}, action: {action}")
        print(f"First few product IDs: {suggested_product_ids[:5] if suggested_product_ids else 'None'}")
        print(f"First few products: {[p.get('id') if isinstance(p, dict) else getattr(p, 'id', None) for p in vector_products[:3]] if vector_products else 'None'}")
        
        return jsonify({
            'response': final_response,
            'suggested_products': vector_products[:10] if len(vector_products) > 0 else [],  # Return up to 10 products
            'suggested_product_ids': suggested_product_ids,  # Return all IDs (already limited to 10)
            'action': action  # 'search_results' will trigger navigation and minimize chat
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

