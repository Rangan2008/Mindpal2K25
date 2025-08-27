# MindPal - Mental Health Support Platform

## Deployment on Render

### Prerequisites
1. A Render account (render.com)
2. A Google Gemini API key
3. (Optional) Twilio account for emergency features

### Deployment Steps

1. **Fork/Clone this repository** to your GitHub account

2. **Create a new Web Service on Render:**
   - Connect your GitHub repository
   - Use the following settings:
     - Environment: Python
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `gunicorn app:app`

3. **Add Environment Variables in Render:**
   ```
   api_key=your_gemini_api_key_here
   FLASK_SECRET_KEY=generate_a_random_secret_key_here
   ```

4. **Add a PostgreSQL Database:**
   - In your Render dashboard, create a new PostgreSQL database
   - Copy the Database URL and add it as an environment variable:
     ```
     DATABASE_URL=your_postgresql_url_here
     ```

5. **Optional - Add Twilio credentials** (for emergency features):
   ```
   account_sid=your_twilio_account_sid
   auth_token=your_twilio_auth_token
   from_number=your_twilio_phone_number
   ```

### Local Development

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd mindpal
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create .env file:**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your actual values.

5. **Run the application:**
   ```bash
   python app.py
   ```

### Features
- User authentication and profiles
- AI-powered chatbot using Google Gemini
- Music therapy recommendations
- Mental health resources
- Emergency contact system
- Goal tracking and wellbeing assessment

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `api_key` | Yes | Google Gemini API key |
| `FLASK_SECRET_KEY` | Yes | Flask session secret key |
| `DATABASE_URL` | No | PostgreSQL URL (auto-provided by Render) |
| `account_sid` | No | Twilio account SID |
| `auth_token` | No | Twilio auth token |
| `from_number` | No | Twilio phone number |
| `PORT` | No | Port number (auto-set by Render) |

### Database
- **Development:** Uses SQLite (automatic)
- **Production:** Uses PostgreSQL (configured via DATABASE_URL)

The app automatically detects the environment and uses the appropriate database.
