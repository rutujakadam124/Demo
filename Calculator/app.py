from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash  # For password hashing
from datetime import datetime
# Initialize Flask app
app = Flask(__name__)
app.secret_key = "supersecretkey" # Used for session encryption
# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/calculator_project_db"
mongo = PyMongo(app)
# Default route redirects to login page
@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])  # Route to handle user registration
def register():
    if request.method == 'POST':
        users = mongo.db.users # Access the 'users' collection
        existing_user = users.find_one({'username': request.form['username']})   # Check if username exists
        if existing_user is None:
            hashpass = generate_password_hash(request.form['password'])      # Hash the password
            users.insert_one({'username': request.form['username'], 'password': hashpass})   # Save user to DB
            return redirect(url_for('login'))  # Redirect to login after successful registration
        return 'Username already exists!'   # Show message if user exists
    return render_template('register.html') # Show registration form

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users # Access 'users' collection
        user = users.find_one({'username': request.form['username']})  # Fetch user by username
        if user and check_password_hash(user['password'], request.form['password']): # Check password using hash comparison
            session['username'] = request.form['username'] # Store username in session
            return redirect(url_for('calculate')) # Redirect to calculator
        return 'Invalid username/password!' # Show error if login fails
    return render_template('login.html')  # Show login form

@app.route('/calculate', methods=['GET', 'POST'])
def calculate():
    if 'username' not in session:   # Ensure user is logged in
        return redirect(url_for('login'))

    result = None  # Initialize result
    if request.method == 'POST':
        op1 = float(request.form['operand1'])  # Get first operand
        op2 = float(request.form['operand2'])  
        operation = request.form['operation']

        if operation == 'add':
            result = op1 + op2
        elif operation == 'sub':
            result = op1 - op2
        elif operation == 'mul':
            result = op1 * op2
        elif operation == 'div':
            result = op1 / op2 if op2 != 0 else 'Cannot divide by zero'

        mongo.db.history.insert_one({
            'username': session['username'],
            'operation': operation,
            'operand1': op1,
            'operand2': op2,
            'result': result,
            'timestamp': datetime.now()
        })
    return render_template('calculate.html', result=result)  # Render calculator page


@app.route('/history/<username>', methods=['GET'])
def history(username):
    records = list(mongo.db.history.find({'username': username}))  # Fetch user history
    return render_template('history.html', records=records)

@app.route('/clear-history/<username>', methods=['GET'])
def clear_history(username):
    mongo.db.history.delete_many({'username': username})   # Delete all user history
    return redirect(url_for('history', username=username))  # Redirect back to history page

# API endpoints for Postman use
@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json()   #Get JSON data from request
    username = data['username']
    op1 = float(data['operand1'])
    op2 = float(data['operand2'])
    operation = data['operation']

    result = None
    if operation == 'add':
        result = op1 + op2
    elif operation == 'sub':
        result = op1 - op2
    elif operation == 'mul':
        result = op1 * op2
    elif operation == 'div':
        result = op1 / op2 if op2 != 0 else 'Cannot divide by zero'

    mongo.db.history.insert_one({
        'username': username,
        'operation': operation,
        'operand1': op1,
        'operand2': op2,
        'result': result,
        'timestamp': datetime.now()
    })

    return jsonify({'result': result})

@app.route('/api/history/<username>', methods=['GET'])
def api_get_history(username):
    records = list(mongo.db.history.find({'username': username}, {'_id': 0}))
    return jsonify(records)

@app.route('/api/clear-history/<username>', methods=['DELETE'])
def api_clear_history(username):
    mongo.db.history.delete_many({'username': username})
    return jsonify({'message': 'History cleared.'})

if __name__ == '__main__':
    app.run(debug=True)
