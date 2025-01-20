from flask import Flask, request, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
import sys
import json
from datetime import datetime
from pymongo import MongoClient
from bson import json_util
import traceback

# Load environment variables from .env file
load_dotenv()

# Debug prints for environment setup
print("Environment Setup:")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"OPENAI_BASE_URL exists: {bool(os.getenv('OPENAI_BASE_URL'))}")
print(f"OPENAI_ORG_ID exists: {bool(os.getenv('OPENAI_ORG_ID'))}")
print(f"MONGODB_URI exists: {bool(os.getenv('MONGODB_URI'))}")

app = Flask(__name__)

def get_db():
    """Get MongoDB connection, creating it if necessary"""
    try:
        mongodb_uri = os.getenv('MONGODB_URI')
        if not mongodb_uri:
            error_msg = "Error: MONGODB_URI not set in environment variables"
            print(error_msg)
            raise Exception(error_msg)

        print(f"Attempting to connect to MongoDB with URI starting with: {mongodb_uri[:20]}...")
        client = MongoClient(mongodb_uri, 
                           serverSelectionTimeoutMS=5000,
                           connectTimeoutMS=5000,
                           socketTimeoutMS=5000)
        
        # Force a connection attempt to verify it works
        client.admin.command('ping')
        db = client.manuscript_analysis
        print("MongoDB connected successfully")
        return db
    except Exception as e:
        error_msg = f"Error connecting to MongoDB: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        raise  # Re-raise the exception to be caught by the caller

def save_email(email):
    try:
        print(f"Attempting to save email: {email}")
        
        # Get fresh DB connection
        db = get_db()  # This may raise an exception now
        if not db:
            error_msg = "Could not connect to MongoDB. URI exists: " + str(bool(os.getenv('MONGODB_URI')))
            print(f"Error: {error_msg}")
            raise Exception(error_msg)
            
        result = db.subscribers.insert_one({
            'email': email,
            'timestamp': datetime.utcnow(),
            'status': 'active'
        })
        
        success = bool(result.inserted_id)
        print(f"Email save {'successful' if success else 'failed'}")
        if not success:
            raise Exception("Failed to get inserted_id from MongoDB")
        return success
    except Exception as e:
        error_msg = f"Error saving email: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        raise  # Re-raise the exception to be caught by the caller

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    try:
        data = request.get_json()
        if not data or 'email' not in data:
            print("Error: Invalid request data - missing email")
            return jsonify({'success': False, 'message': 'Email is required'}), 400
        
        email = data['email']
        print(f"Received subscription request for email: {email}")
        
        # Basic email validation
        if '@' not in email or '.' not in email:
            print(f"Error: Invalid email format - {email}")
            return jsonify({'success': False, 'message': 'Invalid email format'}), 400
        
        if save_email(email):
            print(f"Successfully subscribed email: {email}")
            return jsonify({'success': True, 'message': 'Thank you for subscribing!'})
        else:
            error_msg = "Failed to save email. Database connected: " + str(bool(get_db()))
            print(f"Error: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 500
    except Exception as e:
        error_msg = f"Subscribe error: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        # For debugging, return the actual error message
        return jsonify({'success': False, 'message': error_msg}), 500

def analyze_text(text):
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        org_id = os.getenv('OPENAI_ORG_ID')
        
        if not api_key:
            print("Error: API key not set")
            return {"error": "API key not set. Please check server configuration."}
        if not base_url:
            print("Error: API base URL not set")
            return {"error": "API base URL not set. Please check server configuration."}

        print(f"Making request to: {base_url}")
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ManuscriptAnalysis/1.0'
        }
        
        if org_id:
            headers['X-Organization-ID'] = org_id

        session = requests.Session()
        api_endpoint = f"{base_url}/v1/chat/completions"

        system_prompt = """You are a professional literary agent analyzing manuscripts. 
Provide a concise analysis using EXACTLY this format with these EXACT headings:

COMMERCIAL SCORE: [Score]/10
STRENGTHS:
- [Key strength 1]
- [Key strength 2]
- [Key strength 3]

WEAKNESSES:
- [Key weakness 1]
- [Key weakness 2]
- [Key weakness 3]

GENRES:
- Primary: [Main genre]
- Secondary: [Secondary genre if applicable]

TARGET AUDIENCE:
- [Core demographic description]

COMP TITLES:
- [Title 1 by Author]
- [Title 2 by Author]
- [Title 3 by Author]

Use EXACTLY these headings and bullet points as shown. Keep responses concise but specific."""

        user_prompt = f"Analyze this manuscript excerpt following the EXACT format specified:\n\n{text}"

        data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1000,
            'presence_penalty': 0.3,
            'frequency_penalty': 0.3
        }

        print("Sending request to OpenAI API...")
        try:
            response = session.post(
                api_endpoint,
                headers=headers,
                json=data,
                timeout=8
            )
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {response.headers}")
            
            if response.status_code != 200:
                error_msg = f"API Error: Status {response.status_code}"
                try:
                    error_data = response.json()
                    print(f"Error response data: {error_data}")
                    if 'error' in error_data:
                        error_msg += f" - {error_data['error'].get('message', '')}"
                    else:
                        error_msg += f" - {json.dumps(error_data)}"
                except Exception as e:
                    error_msg += f" - {response.text}"
                    print(f"Error parsing response: {str(e)}")
                print(error_msg)
                return {"error": error_msg}

            response_data = response.json()
            print(f"Response data: {json.dumps(response_data, indent=2)}")
            
            if 'choices' in response_data and len(response_data['choices']) > 0:
                result = response_data['choices'][0]['message']['content']
                print("API Response:", result)
                return {"result": result}
            else:
                error_msg = "Unexpected response format from API"
                print(f"{error_msg}: {json.dumps(response_data, indent=2)}")
                return {"error": error_msg}

        except requests.exceptions.Timeout:
            error_msg = "Request timed out. Please try again with a shorter text."
            print(error_msg)
            return {"error": error_msg}
        except requests.exceptions.RequestException as e:
            error_msg = f"Request error: {str(e)}"
            print(error_msg)
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Error making API request: {str(e)}"
            print(error_msg)
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return {"error": error_msg}

    except Exception as e:
        error_msg = f"Server error in analyze_text: {str(e)}\nType: {type(e)}"
        print(error_msg)
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {"error": error_msg}

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            print("Error: Invalid request data")
            return jsonify({"error": "No text provided"}), 400

        text = data['text']
        if not text or not text.strip():
            print("Error: Empty text provided")
            return jsonify({"error": "Please provide some text to analyze"}), 400

        # Get word count
        word_count = len(text.split())
        if word_count > 1000:
            print(f"Error: Text too long ({word_count} words)")
            return jsonify({"error": "Text is too long. Please keep it under 1000 words."}), 400

        print(f"Analyzing text with {word_count} words...")
        result = analyze_text(text)
        
        if "error" in result:
            print(f"Analysis error: {result['error']}")
            return jsonify(result), 500
            
        print("Analysis completed successfully")
        return jsonify(result)

    except Exception as e:
        error_msg = f"Server error: {str(e)}\nType: {type(e)}"
        print(f"Unexpected error in /analyze: {error_msg}")
        print(f"Exception type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": error_msg}), 500

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                return jsonify({'error': 'No file part'}), 400
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({'error': 'No selected file'}), 400
            
            # Read the file content into memory
            file_content = file.read()
            return jsonify({'message': 'File uploaded successfully!', 'size': len(file_content)})
        except Exception as e:
            error_msg = f"Upload error: {str(e)}\nType: {type(e)}"
            print(error_msg)
            return jsonify({'error': error_msg}), 500
    return render_template('index.html')

@app.route('/subscribers', methods=['GET'])
def get_subscribers():
    try:
        # Check if the request includes a secret key
        secret_key = request.args.get('key')
        if not secret_key or secret_key != os.getenv('ADMIN_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401

        # Get fresh DB connection
        db = get_db()
        if not db:
            return jsonify({'error': 'Database not connected'}), 500

        subscribers = list(db.subscribers.find(
            {'status': 'active'}, 
            {'_id': 0, 'email': 1, 'timestamp': 1}
        ))
        
        # Convert to JSON-serializable format
        subscribers = json.loads(json_util.dumps(subscribers))
        
        return jsonify({
            'count': len(subscribers),
            'subscribers': subscribers
        })
    except Exception as e:
        error_msg = f"Error getting subscribers: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

@app.route('/subscribers/export', methods=['GET'])
def export_subscribers():
    try:
        # Check if the request includes a secret key
        secret_key = request.args.get('key')
        if not secret_key or secret_key != os.getenv('ADMIN_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401

        # Get fresh DB connection
        db = get_db()
        if not db:
            return jsonify({'error': 'Database not connected'}), 500

        subscribers = list(db.subscribers.find(
            {'status': 'active'}, 
            {'_id': 0, 'email': 1, 'timestamp': 1}
        ))
        
        # Create CSV-formatted string
        csv_data = "Email,Timestamp\n"
        for sub in subscribers:
            csv_data += f"{sub['email']},{sub['timestamp']}\n"
        
        # Return as downloadable CSV
        return csv_data, 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment; filename=subscribers.csv'
        }
    except Exception as e:
        error_msg = f"Error exporting subscribers: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        return jsonify({'error': error_msg}), 500

if __name__ == '__main__':
    app.run(debug=True, port=9000)
