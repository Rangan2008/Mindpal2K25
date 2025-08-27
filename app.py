from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, request as flask_request
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime, timedelta
import os
import time
import requests
import json
from twilio.rest import Client
from pymongo import MongoClient
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# Freeze all activity until user logs in or signs up
from functools import wraps

# Place this after app is defined

# Configure Gemini API
genai.configure(api_key=os.environ.get('api_key'))
model = genai.GenerativeModel("gemini-1.5-flash")

# Flask app setup
template_dir = os.path.abspath('Templates')
static_dir = os.path.abspath('Static')


app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret")

# Freeze all activity until user logs in or signs up
from functools import wraps
from flask import request as flask_request

@app.before_request
def require_login():
    allowed_routes = ['auth', 'static', 'health']
    # Allow static files, auth, and health check
    if flask_request.endpoint is not None:
        if (flask_request.endpoint.startswith('static') or
            flask_request.endpoint in allowed_routes):
            return
    # Allow favicon.ico
    if flask_request.path == '/favicon.ico':
        return
    # If not logged in, redirect to login/signup
    if 'username' not in session:
        return redirect(url_for('auth'))

# Debug: Print template folder path
print(f"Template folder path: {app.template_folder}")
print(f"Static folder path: {app.static_folder}")
print(f"Templates directory exists: {os.path.exists(template_dir)}")
print(f"index.html exists: {os.path.exists(os.path.join(template_dir, 'index.html'))}")



# MongoDB Atlas connection (production-ready)
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI environment variable not set. Please set it in your .env or hosting config.")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["wellness_app"]
users_col = db["user"]
chats_col = db["chats"]
emergency_contact_col = db["emergency_contact"]
music_session_col = db["music_session"]
journal_entry_col = db["journal_entry"]
chat_message_col = db["chat_message"]

bcrypt = Bcrypt(app)

# Helper function for Gemini API with retry logic
def generate_ai_response(prompt, max_retries=2):
    """Generate AI response with retry logic for rate limits"""
    for attempt in range(max_retries + 1):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "quota" in error_str.lower():
                if attempt < max_retries:
                    # Wait before retry (exponential backoff)
                    wait_time = (2 ** attempt) * 5  # 5, 10, 20 seconds
                    print(f"Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise Exception("Rate limit exceeded. Please try again later.")
            else:
                raise e
    raise Exception("Max retries exceeded")

# Enhanced playlist fetching functions
def get_mood_playlists(mood):
    """Get curated online playlists based on mood"""
    
    # Real YouTube playlists for different moods
    mood_playlists = {
        'happy': {
            'title': '😊 Happy & Upbeat',
            'description': 'Feel-good music to boost your positive energy and motivation!',
            'color': 'transparent',
            'playlists': [
                {
                    'name': '🎵 Happy Vibes Mix',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOgukzwF8hXrR3VHWS7YqtaUU',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOgukzwF8hXrR3VHWS7YqtaUU',
                    'description': 'Upbeat songs to brighten your day',
                    'duration': '3+ hours',
                    'track_count': '50+'
                },
                {
                    'name': '🌟 Feel Good Hits',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOguP2UBZBKmhWhMZHa3hhc3p',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOguP2UBZBKmhWhMZHa3hhc3p',
                    'description': 'Classic feel-good tracks from various decades',
                    'duration': '4+ hours',
                    'track_count': '75+'
                },
                {
                    'name': '🚗 Road Trip Anthems',
                    'url': 'https://www.youtube.com/playlist?list=PL3oW2tjiIqVwJlOqkMO6pTCd5yrr8rlTM',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PL3oW2tjiIqVwJlOqkMO6pTCd5yrr8rlTM',
                    'description': 'Energetic songs perfect for adventures',
                    'duration': '2+ hours',
                    'track_count': '40+'
                }
            ]
        },
        'stressed': {
            'title': '😰 Stress Relief',
            'description': 'Calming music to help you unwind, relax, and find inner peace.',
            'color': 'transparent',
            'playlists': [
                {
                    'name': '🧘 Deep Relaxation',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7fYoucx5PGcAg3ixthNYTNR',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7fYoucx5PGcAg3ixthNYTNR',
                    'description': 'Ambient sounds for stress relief and meditation',
                    'duration': '8+ hours',
                    'track_count': '100+'
                },
                {
                    'name': '🌊 Ocean Waves',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7ecCHZqgE56DvhXVllTAo_n',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7ecCHZqgE56DvhXVllTAo_n',
                    'description': 'Natural ocean sounds for deep relaxation',
                    'duration': '10+ hours',
                    'track_count': '50+'
                },
                {
                    'name': '🎼 Classical Calm',
                    'url': 'https://www.youtube.com/playlist?list=PLcPOuF2rMF7HB7-QhPb1K8xqtqOXjlhhi',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLcPOuF2rMF7HB7-QhPb1K8xqtqOXjlhhi',
                    'description': 'Peaceful classical music for stress reduction',
                    'duration': '6+ hours',
                    'track_count': '80+'
                }
            ]
        },
        'sad': {
            'title': '😢 Comfort & Healing',
            'description': 'Gentle music to support you through difficult times and emotional healing.',
            'color': 'transparent',
            'playlists': [
                {
                    'name': '💙 Healing Melodies',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOguG1QdMUcbqZhw5DjrW-Ghk',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOguG1QdMUcbqZhw5DjrW-Ghk',
                    'description': 'Gentle acoustic songs for emotional support',
                    'duration': '3+ hours',
                    'track_count': '45+'
                },
                {
                    'name': '🤗 Comfort Songs',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOgtg0V9VFAjgJJ2Q4r6kxJru',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOgtg0V9VFAjgJJ2Q4r6kxJru',
                    'description': 'Soothing ballads for healing and hope',
                    'duration': '2+ hours',
                    'track_count': '35+'
                },
                {
                    'name': '🌧️ Rain & Piano',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7cxpO8NWVdNugWdYTVJ_dha',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7cxpO8NWVdNugWdYTVJ_dha',
                    'description': 'Piano music with rain sounds for reflection',
                    'duration': '4+ hours',
                    'track_count': '60+'
                }
            ]
        },
        'tired': {
            'title': '😴 Rest & Restoration',
            'description': 'Peaceful music to help you recharge, restore energy, and find deep rest.',
            'color': 'transparent',
            'playlists': [
                {
                    'name': '🌙 Sleep Sounds',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7fV20A8t8T6H1qQtOJzJFT3',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7fV20A8t8T6H1qQtOJzJFT3',
                    'description': 'Deep sleep music and binaural beats',
                    'duration': '12+ hours',
                    'track_count': '25+'
                },
                {
                    'name': '💤 Bedtime Stories Music',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOguJK8KNVM19jMbGh18dOiTX',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOguJK8KNVM19jMbGh18dOiTX',
                    'description': 'Gentle instrumental lullabies',
                    'duration': '8+ hours',
                    'track_count': '40+'
                },
                {
                    'name': '🎭 Ambient Restoration',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7doTONsFg5cKYqOOKPFNvJt',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7doTONsFg5cKYqOOKPFNvJt',
                    'description': 'Ambient soundscapes for mental restoration',
                    'duration': '6+ hours',
                    'track_count': '30+'
                }
            ]
        },
        'focused': {
            'title': '🎯 Focus & Concentration',
            'description': 'Music designed to enhance your focus, productivity, and mental clarity.',
            'color': 'transparent',
            'playlists': [
                {
                    'name': '📚 Study Music',
                    'url': 'https://www.youtube.com/playlist?list=PLw-VjHDlEOguHOHSGZN8F8HRsEFzHF_oq',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLw-VjHDlEOguHOHSGZN8F8HRsEFzHF_oq',
                    'description': 'Lo-fi beats and instrumental focus music',
                    'duration': '10+ hours',
                    'track_count': '200+'
                },
                {
                    'name': '🧠 Deep Focus',
                    'url': 'https://www.youtube.com/playlist?list=PLOHoVaTp8R7en3gXqNTMjVs0UjWHlKorq',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLOHoVaTp8R7en3gXqNTMjVs0UjWHlKorq',
                    'description': 'Binaural beats for enhanced concentration',
                    'duration': '5+ hours',
                    'track_count': '20+'
                },
                {
                    'name': '🎼 Classical Focus',
                    'url': 'https://www.youtube.com/playlist?list=PLcPOuF2rMF7H-Wvb7ExagF8tOGNNAyJVH',
                    'embed': 'https://www.youtube.com/embed/videoseries?list=PLcPOuF2rMF7H-Wvb7ExagF8tOGNNAyJVH',
                    'description': 'Classical music proven to enhance focus',
                    'duration': '4+ hours',
                    'track_count': '50+'
                }
            ]
        }
    }
    
    return mood_playlists.get(mood, mood_playlists['happy'])

def detect_crisis_keywords(user_input):
    """Detect if user message contains crisis-related keywords that need immediate attention"""
    crisis_keywords = [
        'suicide', 'kill myself', 'end my life', 'want to die', 'don\'t want to live',
        'hurt myself', 'self harm', 'cutting', 'overdose', 'no point in living',
        'better off dead', 'can\'t go on', 'nothing to live for'
    ]
    
    user_input_lower = user_input.lower()
    return any(keyword in user_input_lower for keyword in crisis_keywords)

def get_crisis_response():
    """Provide immediate crisis support response"""
    return """🚨 I'm very concerned about what you've shared. Your life has value and meaning, and there are people who want to help you right now.

**Please reach out for immediate support:**
• **Crisis Text Line**: Text HOME to 741741
• **National Suicide Prevention Lifeline**: 988 or 1-800-273-8255
• **Campus Counseling Center**: Most colleges offer 24/7 crisis support
• **Emergency Services**: Call 911 if you're in immediate danger

**You are not alone.** These feelings can change with proper support. Please talk to a counselor, trusted friend, family member, or call one of these resources right away.

I care about you and want you to be safe. Would you like me to help you find local mental health resources?"""

def get_fallback_response(user_input):
    """Provide comprehensive, student-focused fallback responses when AI is unavailable"""
    user_input_lower = user_input.lower()
    
    # Greeting responses
    if any(word in user_input_lower for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return "Hello there! 😊 I'm MindPal, your friendly student support assistant. I'm here to help with anything you're dealing with - whether it's academic stress, study tips, personal challenges, or just need someone to talk to. What's on your mind today?"
    
    # Academic stress and exam anxiety
    elif any(word in user_input_lower for word in ['exam', 'test', 'quiz', 'midterm', 'final', 'grade', 'fail', 'performance']):
        return "I understand exam stress can be overwhelming! 📚 Here are some proven strategies: 1) Break study material into smaller chunks, 2) Use active recall and practice tests, 3) Create a realistic study schedule, 4) Take regular breaks (try the Pomodoro technique), 5) Get enough sleep - your brain needs rest to consolidate information. Remember, one exam doesn't define you. You've got this! 💪"
    
    # General stress, anxiety, and mental health
    elif any(word in user_input_lower for word in ['stress', 'anxious', 'worried', 'overwhelmed', 'panic', 'anxiety', 'depressed', 'sad', 'mental health']):
        return "I hear you, and your feelings are completely valid. 🤗 When stress feels overwhelming, try this: 1) Take 5 deep breaths (4 counts in, 6 counts out), 2) Write down what's bothering you, 3) Break big problems into smaller, manageable steps, 4) Reach out to friends, family, or campus counseling services. Remember: it's okay to not be okay, and seeking help is a sign of strength, not weakness. You're not alone in this journey."
    
    # Study tips and learning
    elif any(word in user_input_lower for word in ['study', 'learn', 'focus', 'concentration', 'procrastination', 'distraction', 'homework', 'assignment']):
        return "Great question about studying! 🎯 Here are some effective techniques: 1) **Pomodoro Technique**: 25 min focused study + 5 min break, 2) **Active Learning**: Summarize, teach concepts to others, create flashcards, 3) **Environment**: Find a quiet, dedicated study space, 4) **Schedule**: Study during your peak energy hours, 5) **Breaks**: Regular breaks actually improve retention. For procrastination, start with just 2 minutes - often the hardest part is beginning!"
    
    # Time management
    elif any(word in user_input_lower for word in ['time', 'manage', 'schedule', 'organize', 'deadline', 'busy', 'balance']):
        return "Time management is crucial for student success! ⏰ Try these strategies: 1) **Prioritize** using the Eisenhower Matrix (urgent vs important), 2) **Time-block** your calendar with specific activities, 3) **Use digital tools** like calendars and task apps, 4) **Say no** to non-essential commitments, 5) **Buffer time** for unexpected tasks. Remember: work-life balance isn't perfect balance every day, but rather over time."
    
    # Motivation and encouragement
    elif any(word in user_input_lower for word in ['motivation', 'give up', 'quit', 'tired', 'burnout', 'discouraged']):
        return "I can feel that you're going through a tough time, and that takes courage to acknowledge. 🌟 Remember: every successful person has felt like giving up at some point. What matters is that you're still here, still trying. Try setting tiny, achievable goals today - even small wins build momentum. You've overcome challenges before, and you can do it again. Your future self will thank you for not giving up today. I believe in you! 💙"
    
    # Career and future planning
    elif any(word in user_input_lower for word in ['career', 'job', 'future', 'major', 'graduate', 'internship', 'resume']):
        return "Career planning can feel overwhelming, but remember it's a journey, not a destination! 🚀 Consider: 1) **Explore** your interests through internships, volunteering, informational interviews, 2) **Build skills** relevant to your field, 3) **Network** with professors, alumni, professionals, 4) **Create** a strong LinkedIn profile and resume, 5) **Stay flexible** - career paths often take unexpected turns. Your career counseling center is also a fantastic resource!"
    
    # Financial stress
    elif any(word in user_input_lower for word in ['money', 'financial', 'budget', 'debt', 'loan', 'afford', 'expensive']):
        return "Financial stress is real and affects many students - you're not alone! 💰 Some helpful steps: 1) **Track spending** for a week to see where money goes, 2) **Create a budget** with essentials vs wants, 3) **Look for student discounts** and free campus resources, 4) **Consider part-time work** or campus jobs, 5) **Talk to financial aid** about additional support options. Remember: being financially conscious now sets you up for future success!"
    
    # Social and relationship issues
    elif any(word in user_input_lower for word in ['friends', 'lonely', 'social', 'relationship', 'roommate', 'family']):
        return "Social connections are so important for wellbeing! 🤝 If you're struggling socially: 1) **Join clubs** or activities aligned with your interests, 2) **Be open** to new experiences and meeting different people, 3) **Practice self-compassion** - building friendships takes time, 4) **Quality over quantity** - a few close friends are better than many acquaintances, 5) **Stay connected** with existing support systems. Remember, many students feel lonely sometimes - it's more common than you think!"
    
    # General help and support
    elif any(word in user_input_lower for word in ['help', 'support', 'need', 'advice', 'guidance']):
        return "I'm so glad you reached out for support! 🤗 That shows real self-awareness and strength. I'm here to help with whatever you're going through - academic challenges, stress management, personal concerns, study strategies, career questions, or just need someone to listen. What specific area would you like to talk about? Remember, seeking help is never a sign of weakness - it's how we grow and succeed!"
    
    # Thank you responses
    elif any(word in user_input_lower for word in ['thank', 'thanks', 'appreciate']):
        return "You're so welcome! 😊 I'm really glad I could help. Remember, I'm always here whenever you need support, advice, or just someone to talk to. Keep being amazing, and don't hesitate to reach out anytime you need assistance. You've got this! 🌟"
    
    # Default encouraging response
    else:
        return "Thanks for reaching out! 🌟 I may be temporarily unavailable right now, but I want you to know that whatever you're going through, you're not alone. Every challenge you face is an opportunity to grow stronger. Please try again in a few minutes, and in the meantime, remember to be kind to yourself. You're doing better than you think, and I'm here to support you through whatever comes next! 💙"


# ------------------ ROUTES ------------------
@app.route('/health')
def health_check():
    return "App is running! Template and static folders configured."

@app.route('/')
def home():
    try:
        return render_template('index.html', username=session.get('username'))
    except Exception as e:
        print(f"Error in home route: {e}")
        return f"Error loading home page: {e}", 500

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        form_type = request.form.get('form_type')

        if form_type == 'login':
            email = request.form.get('email')
            password = request.form.get('password')

            user = users_col.find_one({"email": email})

            if user and bcrypt.check_password_hash(user['password'], password):
                session['username'] = user['username']
                session['user_id'] = str(user['_id'])

                # Update last login
                users_col.update_one({"_id": user['_id']}, {"$set": {"last_login": datetime.utcnow()}})

                flash(f"Welcome back, {user['username']}!", "success")
                return redirect(url_for('home'))
            else:
                flash("Invalid email or password", "error")
                return redirect(url_for('auth'))

        elif form_type == 'signup':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm = request.form.get('confirm')

            if password != confirm:
                flash("Passwords do not match", "error")
                return redirect(url_for('auth'))

            if users_col.find_one({"email": email}):
                flash("Email already registered", "error")
                return redirect(url_for('auth'))

            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = {
                "username": username,
                "email": email,
                "password": hashed_pw,
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow()
            }
            users_col.insert_one(new_user)
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('auth'))

    return render_template('registration.html', username=session.get('username'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('is_admin', None)
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route('/profile')
def profile():
    if 'username' not in session:
        flash("Please login to access your profile.", "error")
        return redirect(url_for('auth'))
    return render_template('profile.html', username=session.get('username'))

# Route for goals page
@app.route('/goals')
def goals():
    if 'username' not in session:
        flash("Please login to access your goals.", "error")
        return redirect(url_for('auth'))
    return render_template('goals.html', username=session.get('username'))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    user_input = request.json.get("message", "")
    username = session['username']

    # Check for crisis keywords first
    if detect_crisis_keywords(user_input):
        bot_reply = get_crisis_response()
    else:
        # Generate response using Gemini
        try:
            # Check if API key is configured
            api_key = os.environ.get('api_key')
            if not api_key:
                return jsonify({"error": "API key not configured. Please set the 'api_key' environment variable."}), 500
                
            # Create a comprehensive prompt for student assistance
            student_prompt = f"""You are MindPal, a friendly, empathetic, and knowledgeable AI assistant specifically designed to help students with their academic, personal, and mental health challenges. You should:

1. **Be Conversational & Warm**: Use a friendly, understanding tone. Address students with empathy and genuine care.

2. **Understand Student Context**: Recognize that students face unique challenges like:
   - Academic stress (exams, assignments, grades)
   - Time management and procrastination
   - Financial pressures
   - Social anxiety and peer pressure
   - Mental health concerns (anxiety, depression, burnout)
   - Career uncertainty and future planning
   - Study techniques and learning difficulties
   - Work-life balance

3. **Provide Practical Solutions**: 
   - Offer specific, actionable advice
   - Suggest study techniques, time management strategies
   - Recommend stress relief methods
   - Provide motivational support
   - Share healthy coping mechanisms

4. **Be Supportive but Professional**: 
   - Validate their feelings
   - Encourage seeking professional help when needed
   - Provide resources and next steps
   - Never diagnose or replace professional therapy

5. **Adapt Your Response Style**:
   - For academic questions: Provide study tips, organization methods
   - For stress/anxiety: Offer breathing exercises, mindfulness, coping strategies
   - For motivation: Give encouragement and break down overwhelming tasks
   - For general chat: Be friendly and engaging while staying helpful

Student's message: "{user_input}"

Respond as MindPal with warmth, understanding, and practical help tailored to this student's specific concern."""
            
            bot_reply = generate_ai_response(student_prompt)
            
        except Exception as e:
            error_str = str(e)
            print(f"Gemini API Error: {error_str}")  # Log the error
            
            # Handle quota exceeded error with fallback response
            if "429" in error_str or "quota" in error_str.lower() or "Rate limit exceeded" in error_str:
                bot_reply = get_fallback_response(user_input)
                print("Using fallback response due to rate limit")
            elif "403" in error_str:
                return jsonify({"error": "API access denied. Please check your API key configuration."}), 403
            else:
                bot_reply = get_fallback_response(user_input)
                print("Using fallback response due to API error")

    # Save user message and bot reply to DB
    # Save user message and bot reply to MongoDB
    chats_col.insert_many([
        {"username": username, "message": f"You: {user_input}", "timestamp": datetime.utcnow()},
        {"username": username, "message": f"Bot: {bot_reply}", "timestamp": datetime.utcnow()}
    ])

    return jsonify({"response": bot_reply})

@app.route('/get_chats', methods=['GET'])
def get_chats():
    if 'username' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    username = session['username']
    
    # Get chats from MongoDB
    messages = list(chats_col.find({"username": username}, {"_id": 0}))
    chats = [{"message": msg["message"], "timestamp": msg.get("timestamp", "")} for msg in messages]
    return jsonify({"chats": chats})


@app.route('/api/music/<mood>')
def get_music_data(mood):
    """API endpoint to get music data for a specific mood"""
    # Define music collections based on mood
    music_data = {
        'happy': {
            'title': '😊 Happy & Upbeat',
            'description': 'Feel-good music to boost your positive energy!',
            'color': '#FFD700',
            'tracks': [
                {
                    'name': '🌅 End of Summer',
                    'file': 'end-of-summer.mp3',
                    'description': 'Gentle indie-pop for a cheerful mood.'
                },
                {
                    'name': '🎧 Chasing Daylight',
                    'file': 'chasing-daylight.mp3',
                    'description': 'Instrumental soundtrack with uplifting energy.'
                }
            ],
            'youtube': [
                {
                    'name': '🎵 Upbeat Study Music',
                    'embed': 'https://www.youtube.com/embed/jfKfPfyJRdk',
                    'description': 'Energetic lo-fi beats for productive study sessions'
                },
                {
                    'name': '🌟 Motivational Instrumentals',
                    'embed': 'https://www.youtube.com/embed/tgbNymZ7vqY',
                    'description': 'Piano music to keep you motivated'
                }
            ]
        },
        'stressed': {
            'title': '😰 Stress Relief',
            'description': 'Calming music to help you unwind and relax.',
            'color': '#87CEEB',
            'tracks': [
                {
                    'name': '🌬️ Soft Rain',
                    'file': 'soft-rain.mp3',
                    'description': 'Gentle ambient rain to wash away stress.'
                },
                {
                    'name': '💞 Come Closer',
                    'file': 'come-closer.mp3',
                    'description': 'Soothing vocals for emotional comfort.'
                }
            ],
            'youtube': [
                {
                    'name': '🧘 Deep Relaxation',
                    'embed': 'https://www.youtube.com/embed/1ZYbU82GVz4',
                    'description': 'Guided meditation to release tension'
                },
                {
                    'name': '🌊 Ocean Sounds',
                    'embed': 'https://www.youtube.com/embed/Mk1zL5X1V0Y',
                    'description': 'Natural ocean sounds for stress relief'
                }
            ]
        },
        'sad': {
            'title': '😢 Comfort & Healing',
            'description': 'Gentle music to support you through difficult times.',
            'color': '#DDA0DD',
            'tracks': [
                {
                    'name': '☁️ Dreams',
                    'file': 'dreams.mp3',
                    'description': 'Dreamy ambient sounds for emotional healing.'
                },
                {
                    'name': '🌬️ Soft Breath',
                    'file': 'soft-breath.mp3',
                    'description': 'Gentle melodies to comfort your heart.'
                }
            ],
            'youtube': [
                {
                    'name': '💙 Healing Piano',
                    'embed': 'https://www.youtube.com/embed/tgbNymZ7vqY',
                    'description': 'Soft piano music for emotional support'
                },
                {
                    'name': '🤗 Comforting Nature',
                    'embed': 'https://www.youtube.com/embed/Mk1zL5X1V0Y',
                    'description': 'Peaceful nature sounds for comfort'
                }
            ]
        },
        'tired': {
            'title': '😴 Rest & Restoration',
            'description': 'Peaceful music to help you recharge and find peace.',
            'color': '#E6E6FA',
            'tracks': [
                {
                    'name': '🧘‍♂️ Soft Breath',
                    'file': 'soft-breath.mp3',
                    'description': 'Deep ambient tones for rest and stillness.'
                },
                {
                    'name': '🌬️ Soft Rain',
                    'file': 'soft-rain.mp3',
                    'description': 'Gentle rain sounds for deep relaxation.'
                }
            ],
            'youtube': [
                {
                    'name': '🧠 Sleep Music',
                    'embed': 'https://www.youtube.com/embed/cEQf-NuYc98',
                    'description': 'Binaural beats for deep rest'
                },
                {
                    'name': '🌙 Night Sounds',
                    'embed': 'https://www.youtube.com/embed/e4dT8FJ2GE0',
                    'description': 'Ambient sounds for peaceful sleep'
                }
            ]
        },
        'focused': {
            'title': '🎯 Focus & Concentration',
            'description': 'Music designed to enhance your focus and productivity.',
            'color': '#98FB98',
            'tracks': [
                {
                    'name': '🎧 Chasing Daylight',
                    'file': 'chasing-daylight.mp3',
                    'description': 'Instrumental soundtrack for deep focus.'
                },
                {
                    'name': '☁️ Dreams',
                    'file': 'dreams.mp3',
                    'description': 'Ambient focus music for concentration.'
                }
            ],
            'youtube': [
                {
                    'name': '📚 Study Focus',
                    'embed': 'https://www.youtube.com/embed/jfKfPfyJRdk',
                    'description': 'Lo-fi beats for concentrated study'
                },
                {
                    'name': '🧠 Deep Focus',
                    'embed': 'https://www.youtube.com/embed/cEQf-NuYc98',
                    'description': 'Binaural beats for enhanced concentration'
                }
            ]
        }
    }
    
    # Get the mood data or return error
    selected_mood = music_data.get(mood)
    if not selected_mood:
        return jsonify({"error": "Mood not found"}), 404
    
    return jsonify({
        "mood": mood,
        "data": selected_mood,
        "success": True
    })

@app.route('/api/mood-suggestion', methods=['POST'])
def suggest_mood():
    """API endpoint to suggest mood based on user input"""
    data = request.get_json()
    user_input = data.get('text', '').lower()
    
    # Mood suggestion logic
    mood_keywords = {
        'stressed': ['stress', 'anxious', 'worried', 'overwhelmed', 'pressure', 'exam', 'deadline', 'panic'],
        'sad': ['sad', 'depressed', 'down', 'upset', 'lonely', 'hurt', 'crying', 'heartbreak'],
        'tired': ['tired', 'exhausted', 'sleepy', 'fatigue', 'rest', 'sleep', 'worn out', 'drained'],
        'focused': ['study', 'focus', 'concentrate', 'work', 'productivity', 'assignment', 'project'],
        'happy': ['happy', 'excited', 'good', 'great', 'amazing', 'celebration', 'joy', 'positive']
    }
    
    # Score each mood based on keyword matches
    mood_scores = {}
    for mood, keywords in mood_keywords.items():
        score = sum(1 for keyword in keywords if keyword in user_input)
        if score > 0:
            mood_scores[mood] = score
    
    # Get the mood with highest score
    if mood_scores:
        suggested_mood = max(mood_scores.items(), key=lambda x: x[1])[0]
        confidence = mood_scores[suggested_mood] / len(user_input.split())
    else:
        suggested_mood = 'happy'  # Default to happy if no keywords match
        confidence = 0.1
    
    return jsonify({
        'suggested_mood': suggested_mood,
        'confidence': min(confidence, 1.0),
        'music_url': f'/music/{suggested_mood}',
        'api_url': f'/api/music/{suggested_mood}',
        'success': True
    })

# ------------------ JOURNAL API ROUTES ------------------
@app.route('/api/journal/save', methods=['POST'])
def save_journal_entry():
    """Save a new journal entry for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    try:
        data = request.json
        content = data.get('content', '').strip()
        mood = data.get('mood', None)
        if not content:
            return jsonify({'success': False, 'error': 'Journal content cannot be empty'}), 400
        entry = {
            'user_id': session['user_id'],
            'content': content,
            'mood': mood,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        result = journal_entry_col.insert_one(entry)
        return jsonify({
            'success': True,
            'message': 'Journal entry saved successfully!',
            'entry_id': str(result.inserted_id),
            'created_at': entry['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/journal/entries', methods=['GET'])
def get_journal_entries():
    """Get all journal entries for the current user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'User not logged in'}), 401
    
    try:
        entries = list(journal_entry_col.find({'user_id': session['user_id']}).sort('created_at', -1))
        entries_data = []
        for entry in entries:
            entries_data.append({
                'id': str(entry['_id']),
                'content': entry['content'],
                'mood': entry.get('mood'),
                'created_at': entry['created_at'].strftime('%Y-%m-%d %H:%M:%S') if 'created_at' in entry else None,
                'updated_at': entry['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if 'updated_at' in entry else None
            })
        return jsonify({
            'success': True,
            'entries': entries_data,
            'count': len(entries_data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ------------------ ADDITIONAL PAGES ------------------
@app.route('/wellbeing')
def wellbeing():
    return render_template('wellbeing.html', username=session.get('username'))

@app.route('/studytips')
def studytips():
    return render_template('studytips.html', username=session.get('username'))

@app.route('/music')
def music():
    return render_template('music.html', username=session.get('username'))

@app.route('/music/<mood>')
def music_by_mood(mood):
    # Get real online playlists for the mood
    mood_data = get_mood_playlists(mood)
    
    return render_template('music.html', 
                         username=session.get('username'),
                         mood_data=mood_data,
                         current_mood=mood,
                         all_moods=['happy', 'stressed', 'sad', 'tired', 'focused'])

# New API endpoints for enhanced music functionality
@app.route('/api/mood-playlists/<mood>')
def get_mood_playlists_api(mood):
    """API endpoint to get mood playlists (for AJAX calls)"""
    mood_data = get_mood_playlists(mood)
    return jsonify(mood_data)

@app.route('/api/mood-config')
def get_mood_config():
    """API endpoint to get complete mood configuration for the frontend"""
    mood_config = {
        'happy': {
            'title': '😊 Happy & Upbeat',
            'subtitle': 'Feel-good music to boost your positive energy and motivation!',
            'playlists': [
                {
                    'name': '🎵 Happy Vibes Collection',
                    'description': 'Upbeat songs to brighten your day',
                    'url': 'https://www.youtube.com/playlist?list=PLGtD-HOt3wYA8CK0pQB98y-0MD84KDago',
                    'embed': 'PLGtD-HOt3wYA8CK0pQB98y-0MD84KDago'
                },
                {
                    'name': '🌟 Feel Good Hits',
                    'description': 'Classic feel-good tracks from various decades',
                    'url': 'https://www.youtube.com/playlist?list=PLm8013_gmOkhPPLyfnk1P7_o3top0a1Z5',
                    'embed': 'PLm8013_gmOkhPPLyfnk1P7_o3top0a1Z5'
                },
                {
                    'name': '🚀 Energy Boost',
                    'description': 'High-energy music for motivation',
                    'url': 'https://www.youtube.com/playlist?list=PL9G8zyZl8ZRZdemxh4wjqliFnUuE08ETj',
                    'embed': 'PL9G8zyZl8ZRZdemxh4wjqliFnUuE08ETj'
                }
            ],
            'audioFiles': [
                {'name': 'End of Summer', 'file': 'end-of-summer.mp3', 'description': 'Uplifting indie melody'},
                {'name': 'Chasing Daylight', 'file': 'chasing-daylight.mp3', 'description': 'Energetic instrumental'}
            ]
        },
        'stressed': {
            'title': '😰 Stress Relief',
            'subtitle': 'Calming music to help you unwind, relax, and find inner peace',
            'playlists': [
                {
                    'name': '🧘 Deep Relaxation',
                    'description': 'Ambient sounds for stress relief and meditation',
                    'url': 'https://www.youtube.com/playlist?list=PLwslHpp7T0WVnDhw8_5cXWnWGWLuqC9eB',
                    'embed': 'PLwslHpp7T0WVnDhw8_5cXWnWGWLuqC9eB'
                },
                {
                    'name': '🌊 Nature Sounds',
                    'description': 'Natural sounds for deep relaxation',
                    'url': 'https://www.youtube.com/playlist?list=PLPabdEIQxVqAuGRr1o7PG8wfq0fHJZNwa',
                    'embed': 'PLPabdEIQxVqAuGRr1o7PG8wfq0fHJZNwa'
                },
                {
                    'name': '🎼 Calm Classical',
                    'description': 'Peaceful classical music for stress reduction',
                    'url': 'https://www.youtube.com/playlist?list=PLSXC1QOKVgMyD7psQn2OgGNX6mdI0lH6E',
                    'embed': 'PLSXC1QOKVgMyD7psQn2OgGNX6mdI0lH6E'
                }
            ],
            'audioFiles': [
                {'name': 'Soft Rain', 'file': 'soft-rain.mp3', 'description': 'Gentle rain sounds for relaxation'},
                {'name': 'Come Closer', 'file': 'come-closer.mp3', 'description': 'Soothing vocals for comfort'},
                {'name': 'Soft Breath', 'file': 'soft-breath.mp3', 'description': 'Meditative breathing sounds'}
            ]
        },
        'sad': {
            'title': '😢 Comfort & Healing',
            'subtitle': 'Gentle music to support you through difficult times and emotional healing',
            'playlists': [
                {
                    'name': '💙 Healing Melodies',
                    'description': 'Gentle songs for emotional support',
                    'url': 'https://www.youtube.com/playlist?list=PL8srLQTE6oR3GBTwnE22mj2UrFzFK_tPs',
                    'embed': 'PL8srLQTE6oR3GBTwnE22mj2UrFzFK_tPs'
                },
                {
                    'name': '🤗 Comfort Songs',
                    'description': 'Soothing ballads for healing and hope',
                    'url': 'https://www.youtube.com/playlist?list=PLY022uAkaO1uPLPlewXmamFwB1T9DgftD',
                    'embed': 'PLY022uAkaO1uPLPlewXmamFwB1T9DgftD'
                },
                {
                    'name': '🌧️ Emotional Support',
                    'description': 'Music for processing emotions',
                    'url': 'https://www.youtube.com/playlist?list=PLLlb2C74bLzdu9dUe9QiuCMq-cLJtIbDZ',
                    'embed': 'PLLlb2C74bLzdu9dUe9QiuCMq-cLJtIbDZ'
                }
            ],
            'audioFiles': [
                {'name': 'Dreams', 'file': 'dreams.mp3', 'description': 'Dreamy ambient sounds for healing'},
                {'name': 'Come Closer', 'file': 'come-closer.mp3', 'description': 'Comforting vocal melodies'}
            ]
        },
        'tired': {
            'title': '😴 Rest & Restoration',
            'subtitle': 'Peaceful music to help you recharge, restore energy, and find deep rest',
            'playlists': [
                {
                    'name': '🌙 Sleep Sounds',
                    'description': 'Deep sleep music and relaxing sounds',
                    'url': 'https://www.youtube.com/playlist?list=PLhAM4Z6_ykycC_78-gs82Hck4bfj7oMLw',
                    'embed': 'PLhAM4Z6_ykycC_78-gs82Hck4bfj7oMLw'
                },
                {
                    'name': '💤 Night Time Relief',
                    'description': 'Gentle sounds for peaceful rest',
                    'url': 'https://www.youtube.com/playlist?list=PL_A9MFp93jdKb96tSPmNAlnFJJPc9MOp-',
                    'embed': 'PL_A9MFp93jdKb96tSPmNAlnFJJPc9MOp-'
                },
                {
                    'name': '🛌 Bedtime Music',
                    'description': 'Ambient music for deep restoration',
                    'url': 'https://www.youtube.com/playlist?list=PLeq5deLX90_fCIoHVtWowBrhpHFYh4nHW',
                    'embed': 'PLeq5deLX90_fCIoHVtWowBrhpHFYh4nHW'
                }
            ],
            'audioFiles': [
                {'name': 'Soft Breath', 'file': 'soft-breath.mp3', 'description': 'Deep meditation for rest'},
                {'name': 'Soft Rain', 'file': 'soft-rain.mp3', 'description': 'Gentle rain for sleep'},
                {'name': 'Dreams', 'file': 'dreams.mp3', 'description': 'Ambient sounds for restoration'}
            ]
        },
        'focused': {
            'title': '🎯 Focus & Concentration',
            'subtitle': 'Music designed to enhance your focus, productivity, and mental clarity',
            'playlists': [
                {
                    'name': '📚 Study Focus',
                    'description': 'Lo-fi beats and focus music for studying',
                    'url': 'https://www.youtube.com/playlist?list=PLOzlQzU-yr65nTKt7tEbHBnhZhU_5bVG',
                    'embed': 'PLOzlQzU-yr65nTKt7tEbHBnhZhU_5bVG'
                },
                {
                    'name': '🧠 Deep Concentration',
                    'description': 'Instrumental music for deep focus',
                    'url': 'https://www.youtube.com/playlist?list=PLqiHsh_gQp2S8-NXpUwNHQyDgAi2WBpiE',
                    'embed': 'PLqiHsh_gQp2S8-NXpUwNHQyDgAi2WBpiE'
                },
                {
                    'name': '⚡ Productivity Boost',
                    'description': 'Energizing music for enhanced productivity',
                    'url': 'https://www.youtube.com/playlist?list=PLSE6xYINkIG6-ILoq8jxSUBnhZhU_5bVG',
                    'embed': 'PLSE6xYINkIG6-ILoq8jxSUBnhZhU_5bVG'
                }
            ],
            'audioFiles': [
                {'name': 'Chasing Daylight', 'file': 'chasing-daylight.mp3', 'description': 'Instrumental focus music'},
                {'name': 'Dreams', 'file': 'dreams.mp3', 'description': 'Ambient concentration sounds'}
            ]
        }
    }
    return jsonify(mood_config)

@app.route('/api/music-session/start', methods=['POST'])
def start_music_session_enhanced():
    """Start a new music session with enhanced tracking (MongoDB)"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    mood = data.get('mood', 'unknown')
    playlist_name = data.get('playlist_name', 'Unknown Playlist')
    playlist_url = data.get('playlist_url', '')
    user = users_col.find_one({'username': session['username']})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    session_doc = {
        'user_id': str(user['_id']),
        'mood': mood,
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'start_time': datetime.utcnow(),
        'session_completed': False
    }
    result = music_session_col.insert_one(session_doc)
    return jsonify({
        'session_id': str(result.inserted_id),
        'message': 'Enhanced music session started successfully',
        'mood': mood,
        'playlist_name': playlist_name
    })

@app.route('/api/music-session/end', methods=['POST'])
def end_music_session_enhanced():
    """End the current music session (MongoDB)"""
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = users_col.find_one({'username': session['username']})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    # Find most recent active session
    session_doc = music_session_col.find_one({
        'user_id': str(user['_id']),
        'end_time': {'$exists': False},
        'session_completed': False
    }, sort=[('start_time', -1)])
    if session_doc:
        end_time = datetime.utcnow()
        duration = (end_time - session_doc['start_time']).total_seconds() / 60
        music_session_col.update_one({'_id': session_doc['_id']}, {
            '$set': {
                'end_time': end_time,
                'duration_minutes': duration,
                'session_completed': True
            }
        })
        return jsonify({
            'message': 'Session ended successfully',
            'duration_minutes': round(duration, 2),
            'mood': session_doc.get('mood', '')
        })
    return jsonify({'message': 'No active session found'})

# New API endpoints for session tracking
@app.route('/api/music/start_session', methods=['POST'])
def start_music_session():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    mood = data.get('mood')
    playlist_name = data.get('playlist_name')
    playlist_url = data.get('playlist_url')
    user = users_col.find_one({'username': session['username']})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    session_doc = {
        'user_id': str(user['_id']),
        'mood': mood,
        'playlist_name': playlist_name,
        'playlist_url': playlist_url,
        'start_time': datetime.utcnow(),
        'session_completed': False
    }
    result = music_session_col.insert_one(session_doc)
    return jsonify({
        'session_id': str(result.inserted_id),
        'message': 'Session started successfully'
    })

@app.route('/api/music/end_session', methods=['POST'])
def end_music_session():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    data = request.get_json()
    session_id = data.get('session_id')
    session_doc = music_session_col.find_one({'_id': ObjectId(session_id)})
    if not session_doc:
        return jsonify({'error': 'Session not found'}), 404
    end_time = datetime.utcnow()
    duration = (end_time - session_doc['start_time']).total_seconds() / 60
    music_session_col.update_one({'_id': session_doc['_id']}, {
        '$set': {
            'end_time': end_time,
            'duration_minutes': duration,
            'session_completed': True
        }
    })
    return jsonify({
        'message': 'Session ended successfully',
        'duration_minutes': duration
    })

@app.route('/api/music/session_stats')
def get_session_stats():
    if 'username' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    user = users_col.find_one({'username': session['username']})
    if not user:
        return jsonify({'error': 'User not found'}), 404
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    sessions = list(music_session_col.find({
        'user_id': str(user['_id']),
        'start_time': {'$gte': thirty_days_ago},
        'session_completed': True
    }))
    total_sessions = len(sessions)
    total_minutes = sum(s.get('duration_minutes', 0) for s in sessions)
    mood_breakdown = {}
    for session in sessions:
        mood = session.get('mood', 'unknown')
        mood_breakdown[mood] = mood_breakdown.get(mood, 0) + 1
    return jsonify({
        'total_sessions': total_sessions,
        'total_minutes': round(total_minutes, 1),
        'total_hours': round(total_minutes / 60, 1),
        'mood_breakdown': mood_breakdown,
        'average_session_minutes': round(total_minutes / max(total_sessions, 1), 1)
    })

@app.route('/academic')
def academic():
    return render_template('Academic.html', username=session.get('username'))

@app.route('/financial')
def financial():
    return render_template('Financial.html', username=session.get('username'))

@app.route('/career')
def career():
    return render_template('career.html', username=session.get('username'))

@app.route('/time')
def time():
    return render_template('time.html', username=session.get('username'))

@app.route('/pmh')
def pmh():
    return render_template('pmh.html', username=session.get('username'))

@app.route('/chat')
def chat_page():
    return render_template('chatbot.html', username=session.get('username'))

@app.route('/emergency')
def emergency_page():
    return render_template('emergency.html', username=session.get('username'))


from flask import render_template, request, redirect, url_for, session, flash

@app.route('/emergency', methods=['GET', 'POST'])
def emergency():
    if 'username' not in session:
        flash('Please log in to access emergency features.', 'danger')
        return redirect(url_for('auth'))
    username = session['username']
    user = users_col.find_one({'username': username})
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('auth'))
    user_id = str(user['_id'])
    # Save a new number
    if request.method == 'POST' and 'save_number' in request.form:
        new_number = request.form['new_number']
        if new_number:
            emergency_contact_col.insert_one({'user_id': user_id, 'phone_number': new_number})
            flash('Emergency contact saved!', 'success')
    # Send emergency message
    if request.method == 'POST' and 'send_alert' in request.form:
        contacts = list(emergency_contact_col.find({'user_id': user_id}))
        if not contacts:
            flash('No emergency contacts found. Please add a contact first.', 'warning')
        else:
            account_sid = os.environ.get('account_sid')
            auth_token = os.environ.get('auth_token')
            from_number = os.environ.get('from_number')
            if not account_sid or not auth_token or not from_number:
                flash('Twilio credentials not configured. Please check your .env file.', 'danger')
            elif account_sid.startswith('your_') or auth_token.startswith('your_') or from_number.startswith('your_'):
                flash('Please update your Twilio credentials in the .env file with real values.', 'danger')
            else:
                try:
                    client = Client(account_sid, auth_token)
                    success_count = 0
                    for contact in contacts:
                        try:
                            message = client.messages.create(
                                body="🚨 Emergency Alert: Please check on your child immediately! From MindPal.",
                                from_=from_number,
                                to=contact['phone_number']
                            )
                            success_count += 1
                            print(f"SMS sent successfully to {contact['phone_number']}. Message SID: {message.sid}")
                        except Exception as e:
                            print(f"Failed to send SMS to {contact['phone_number']}: {str(e)}")
                            flash(f"Failed to send SMS to {contact['phone_number']}: {str(e)}", 'danger')
                    if success_count > 0:
                        flash(f'Emergency alerts sent to {success_count} contact(s)!', 'success')
                except Exception as e:
                    print(f"Twilio Client Error: {str(e)}")
                    flash(f"Error initializing Twilio client: {str(e)}", 'danger')
    # Get stored contacts
    contacts = list(emergency_contact_col.find({'user_id': user_id}))
    return render_template('emergency.html', contacts=contacts)


# ------------------ MAIN ------------------
if __name__ == '__main__':
    # No DB table creation needed for MongoDB
    port = int(os.environ.get('PORT', 10000))  # Render/Railway use $PORT
    app.run(host='0.0.0.0', port=port, debug=False)
