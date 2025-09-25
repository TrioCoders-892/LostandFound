# Profile page

from flask import Flask, render_template, request, redirect, session, url_for, flash
from flask_pymongo import PyMongo
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
import os
import datetime

app = Flask(__name__)
app.secret_key = "secret_key_here"

# MongoDB Atlas configuration
app.config["MONGO_URI"] = "mongodb+srv://flaskuser:flaskpass123@cluster0.jmab4ig.mongodb.net/lost_found_db?retryWrites=true&w=majority"

mongo = PyMongo(app)

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Helper to check allowed image extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/items', methods=['GET', 'POST'])
def index():
    query = {}
    if request.method == 'POST':
        status = request.form.get('status')
        keyword = request.form.get('keyword')
        block = request.form.get('block')
        if status and status != "all":
            query["status"] = status
        if block and block != "all":
            query["block"] = block
        if keyword:
            query["$or"] = [{"title": {"$regex": keyword, "$options": "i"}},
                             {"location": {"$regex": keyword, "$options": "i"}}]
    items = list(mongo.db.items.find(query).sort("date_reported", -1))
    # Attach username to each item
    for item in items:
        user = mongo.db.users.find_one({"_id": ObjectId(item["user_id"])});
        item["username"] = user["username"] if user else "Unknown"
    return render_template('index.html', items=items)

# Register
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        # Enforce email domain restriction
        if not email.endswith('@nbkrist.org'):
            flash("Registration allowed only with @nbkrist.org email addresses.", "danger")
            return redirect(url_for('register'))
        password = generate_password_hash(request.form['password'])
        if mongo.db.users.find_one({"email": email}):
            flash("Email already exists!", "danger")
            return redirect(url_for('register'))
        mongo.db.users.insert_one({"username": username, "email": email, "password": password})
        flash("Registration Successful!","success")
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='POST':
        email=request.form['email']
        password=request.form['password']
        user = mongo.db.users.find_one({"email": email})
        if user and check_password_hash(user['password'], password):
            session['user_id'] = str(user['_id'])
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid Credentials","danger")
    return render_template('login.html')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        items = list(mongo.db.items.find().sort("date_reported", -1))
        for item in items:
            user = mongo.db.users.find_one({"_id": ObjectId(item["user_id"])});
            item["username"] = user["username"] if user else "Unknown"
        return render_template('dashboard.html', items=items)
    return redirect(url_for('login'))

# Add Item
@app.route('/add_item', methods=['GET','POST'])
def add_item():
    if 'user_id' in session:
        if request.method=='POST':
            title = request.form['title']
            description = request.form['description']
            status = request.form['status']
            location = request.form['location']
            block = request.form['block']

            file = request.files['image']
            filename = None
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            mongo.db.items.insert_one({
                "user_id": session['user_id'],
                "title": title,
                "description": description,
                "status": status,
                "location": location,
                "block": block,
                "image": filename,
                "date_reported": datetime.datetime.utcnow()
            })
            flash("Item added successfully!", "success")
            return redirect(url_for('dashboard'))
        return render_template('add_item.html')
    return redirect(url_for('login'))

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('landing'))


# View all lost items
@app.route('/view_lost_items')
def view_lost_items():
    items = list(mongo.db.items.find({"status": "lost"}).sort("date_reported", -1))
    for item in items:
        user = mongo.db.users.find_one({"_id": ObjectId(item["user_id"])});
        item["username"] = user["username"] if user else "Unknown"
    return render_template('view_items.html', items=items, title="Lost Items")

# View all found items
@app.route('/view_found_items')
def view_found_items():
    items = list(mongo.db.items.find({"status": "found"}).sort("date_reported", -1))
    for item in items:
        user = mongo.db.users.find_one({"_id": ObjectId(item["user_id"])});
        item["username"] = user["username"] if user else "Unknown"
    return render_template('view_items.html', items=items, title="Found Items")

# Mark item as found
@app.route('/mark_found/<item_id>', methods=['POST'])
def mark_found(item_id):
    if 'user_id' in session:
        item = mongo.db.items.find_one({"_id": ObjectId(item_id), "user_id": session['user_id']})
        if item:
            mongo.db.items.delete_one({"_id": ObjectId(item_id)})
            flash("Item removed from database as found.", "success")
        else:
            flash("Item not found or unauthorized.", "danger")
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Test DB connection
@app.route('/test_db')
def test_db():
    users = list(mongo.db.users.find())
    items = list(mongo.db.items.find())
    return {"users": users, "items": items}

# ==================== MESSAGING SYSTEM ====================

# Inbox - View all conversations
@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get all messages where user is sender or receiver
    sent_messages = list(mongo.db.messages.find({"sender_id": ObjectId(session['user_id'])}).sort("timestamp", -1))
    received_messages = list(mongo.db.messages.find({"receiver_id": ObjectId(session['user_id'])}).sort("timestamp", -1))

    # Combine and get unique conversations
    conversations = {}
    for msg in sent_messages + received_messages:
        item_id = str(msg['item_id'])
        if item_id not in conversations:
            conversations[item_id] = {
                'item': mongo.db.items.find_one({"_id": msg['item_id']}),
                'last_message': msg,
                'unread_count': 0
            }

    # Count unread messages
    for item_id in conversations:
        unread_count = mongo.db.messages.count_documents({
            "item_id": ObjectId(item_id),
            "receiver_id": ObjectId(session['user_id']),
            "read": False
        })
        conversations[item_id]['unread_count'] = unread_count

    return render_template('inbox.html', conversations=conversations)

# Conversation - View messages for specific item
@app.route('/conversation/<item_id>')
def conversation(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = mongo.db.items.find_one({"_id": ObjectId(item_id)})
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for('inbox'))

    # Get all messages for this item (full thread)
    messages = list(mongo.db.messages.find({
        "item_id": ObjectId(item_id)
    }).sort("timestamp", 1))

    # Mark messages as read
    mongo.db.messages.update_many({
        "item_id": ObjectId(item_id),
        "receiver_id": ObjectId(session['user_id']),
        "read": False
    }, {"$set": {"read": True}})

    # Get the other user (item owner if current user is finder, or vice versa)
    other_user_id = item['user_id'] if item['user_id'] != session['user_id'] else None
    if other_user_id:
        other_user = mongo.db.users.find_one({"_id": ObjectId(other_user_id)})
    else:
        other_user = None

    # Build users dictionary for all message senders
    user_ids = set(str(msg['sender_id']) for msg in messages)
    users = {}
    for uid in user_ids:
        user_obj = mongo.db.users.find_one({"_id": ObjectId(uid)})
        if user_obj:
            users[uid] = {"username": user_obj["username"], "email": user_obj["email"]}
        else:
            users[uid] = {"username": "Unknown", "email": ""}

    return render_template('conversation.html', item=item, messages=messages, other_user=other_user, users=users)

# Send message
@app.route('/send_message/<item_id>', methods=['POST'])
def send_message(item_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    item = mongo.db.items.find_one({"_id": ObjectId(item_id)})
    if not item:
        flash("Item not found.", "danger")
        return redirect(url_for('index'))

    message_text = request.form.get('message')
    if not message_text:
        flash("Message cannot be empty.", "danger")
        return redirect(url_for('conversation', item_id=item_id))

    # Determine receiver: if current user is owner, send to contacting user; else send to owner
    if item['user_id'] == session['user_id']:
        # Owner replying: find the other user in the conversation
        last_message = mongo.db.messages.find_one({
            "item_id": ObjectId(item_id),
            "sender_id": {"$ne": ObjectId(session['user_id'])}
        }, sort=[("timestamp", -1)])
        if last_message:
            receiver_id = last_message['sender_id']
        else:
            flash("No user to reply to yet.", "danger")
            return redirect(url_for('conversation', item_id=item_id))
    else:
        # Non-owner: send to owner
        receiver_id = item['user_id']

    # Insert message
    mongo.db.messages.insert_one({
        "item_id": ObjectId(item_id),
        "sender_id": ObjectId(session['user_id']),
        "receiver_id": ObjectId(receiver_id),
        "message": message_text,
        "timestamp": datetime.datetime.utcnow(),
        "read": False
    })

    flash("Message sent successfully!", "success")
    return redirect(url_for('conversation', item_id=item_id))

# Mark message as read
@app.route('/mark_message_read/<message_id>', methods=['POST'])
def mark_message_read(message_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    mongo.db.messages.update_one({
        "_id": ObjectId(message_id),
        "receiver_id": ObjectId(session['user_id'])
    }, {"$set": {"read": True}})

    return {"success": True}

if __name__=='__main__':
    app.run(debug=True)
