from flask import Flask, request, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
import sys
import json
from datetime import datetime

# Print current working directory and absolute path to .env
print(f"Current working directory: {os.getcwd()}")
print(f"Looking for .env file in: {os.path.abspath('.env')}")

# Load environment variables from .env file
load_dotenv()

# Debug prints
print(f"Environment variables loaded")
print(f"API Key exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"Base URL: {os.getenv('OPENAI_BASE_URL')}")
if os.getenv('OPENAI_API_KEY'):
    print(f"API Key value: {os.getenv('OPENAI_API_KEY')[:10]}...")  # Only print first 10 chars for security

app = Flask(__name__)

# Set upload folder
UPLOAD_FOLDER = 'uploads/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def save_email(email):
    try:
        with open('user_emails.txt', 'a') as f:
            signup_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{email},{signup_date}\n")
        return True
    except Exception as e:
        print(f"Error saving email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json.get('email')
    if not email:
        return jsonify({'success': False, 'message': 'Email is required'}), 400
    
    # Basic email validation
    if '@' not in email or '.' not in email:
        return jsonify({'success': False, 'message': 'Invalid email format'}), 400
    
    if save_email(email):
        return jsonify({'success': True, 'message': 'Thank you for subscribing!'})
    else:
        return jsonify({'success': False, 'message': 'Error saving email'}), 500

def analyze_text(text):
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        
        if not api_key:
            return "Error: API key not set. Please add your API key to the .env file."
        if not base_url:
            return "Error: API base URL not set. Please add the base URL to the .env file."

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ManuscriptAnalysis/1.0',
            'X-Organization-ID': os.getenv('OPENAI_ORG_ID', '')
        }

        session = requests.Session()
        api_endpoint = f"{base_url}/v1/chat/completions"

        prompt = f"""Analyze the following query letter or excerpt and provide a detailed analysis in the following format:

        Commercial Viability Score (1-10)
        - Overall Score: [number]/10
        - Strengths: List key commercial strengths
        - Weaknesses: List potential market challenges
        - Critical Analysis: Brutally honest assessment of commercial potential
        
        Primary Genres
        - List each genre
        
        Subgenres
        - List each subgenre
        
        Tropes
        - List prominent tropes
        
        Tone
        - List tonal elements
        
        Target Audience
        - Describe the primary audience
        - List any secondary audiences
        
        Themes
        - List major themes
        
        Unique Hooks/Selling Points
        - List unique elements that make this story stand out
        
        Similar Published Books (3-5 titles)
        - Title by Author (Year) - Estimated Sales: [number] copies (if available). Brief explanation of similarities
        
        Text to analyze:
        {text}
        """

        data = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': 'You are a professional literary agent and publishing expert.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }

        response = session.post(
            api_endpoint,
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            error_msg = f"API Error: Status {response.status_code}"
            try:
                error_data = response.json()
                if 'error' in error_data:
                    error_msg += f" - {error_data['error'].get('message', '')}"
                else:
                    error_msg += f" - {json.dumps(error_data)}"
            except:
                error_msg += f" - {response.text}"
            print(error_msg)  # Log the error
            return error_msg

        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            print(f"Unexpected response format: {json.dumps(response_data, indent=2)}")
            return "Error: Unexpected response format from API"

    except Exception as e:
        print(f"Error in analyze_text: {str(e)}")  # Log the error
        return f"Error: {str(e)}"

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    result = analyze_text(data['text'])
    print(f"Analysis result: {result}")  # Log the result
    return jsonify({'result': result})

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        # Read the file content into memory
        file_content = file.read()
        # Process the file content as needed (e.g., analyze it)
        return jsonify({'message': 'File uploaded successfully!', 'size': len(file_content)})
    return render_template('index.html')

if __name__ == '__main__':
    print("\nStarting server on port 9000...")
    app.run(debug=True, port=9000)
