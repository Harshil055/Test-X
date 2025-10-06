from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

# In-memory storage for products
products = {}
next_id = 1

# Helper function to validate product data
def validate_product(data):
    errors = []
    
    if 'name' not in data or not data['name']:
        errors.append('Name is required')
    
    if 'description' not in data or not data['description']:
        errors.append('Description is required')
    
    if 'stock' not in data:
        errors.append('Stock is required')
    elif not isinstance(data['stock'], int) or data['stock'] < 0:
        errors.append('Stock must be a non-negative integer')
    
    if 'price' not in data:
        errors.append('Price is required')
    elif not isinstance(data['price'], (int, float)) or data['price'] < 0:
        errors.append('Price must be a non-negative number')
    
    return errors

# CREATE - Add a new product
@app.route('/products', methods=['POST'])
def create_product():
    global next_id
    
    data = request.get_json()
    
    # Validate data
    errors = validate_product(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Create product
    product = {
        'id': next_id,
        'name': data['name'],
        'description': data['description'],
        'stock': data['stock'],
        'price': data['price'],
        'created_at': datetime.now().isoformat()
    }
    
    products[next_id] = product
    next_id += 1
    
    return jsonify(product), 201

# READ - Get all products
@app.route('/products', methods=['GET'])
def get_products():
    return jsonify(list(products.values())), 200

# READ - Get a single product by ID
@app.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = products.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(product), 200

# UPDATE - Update a product by ID
@app.route('/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    product = products.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.get_json()
    
    # Validate data
    errors = validate_product(data)
    if errors:
        return jsonify({'error': 'Validation failed', 'details': errors}), 400
    
    # Update product
    product['name'] = data['name']
    product['description'] = data['description']
    product['stock'] = data['stock']
    product['price'] = data['price']
    product['updated_at'] = datetime.now().isoformat()
    
    return jsonify(product), 200

# DELETE - Delete a product by ID
@app.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    product = products.get(product_id)
    
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    del products[product_id]
    
    return jsonify({'message': 'Product deleted successfully'}), 200

# Root endpoint
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'message': 'Product API',
        'endpoints': {
            'GET /products': 'Get all products',
            'GET /products/<id>': 'Get a product by ID',
            'POST /products': 'Create a new product',
            'PUT /products/<id>': 'Update a product by ID',
            'DELETE /products/<id>': 'Delete a product by ID'
        }
    }), 200

if __name__ == '__main__':
    app.run(debug=True, port=5000)