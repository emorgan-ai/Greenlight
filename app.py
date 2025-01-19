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
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    org_id = os.getenv('OPENAI_ORG_ID')

    if not api_key:
        return "Error: OpenAI API key not set. Please add your API key to the .env file."
    if not base_url:
        return "Error: OpenAI base URL not set. Please add the base URL to the .env file."

    try:
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
        - Title by Author (Year) - Estimated Sales: [number] copies (if available). Brief explanation of similarities
        - Title by Author (Year) - Estimated Sales: [number] copies (if available). Brief explanation of similarities
        - Title by Author (Year) - Estimated Sales: [number] copies (if relevant). Brief explanation of similarities
        - Title by Author (Year) - Estimated Sales: [number] copies (if relevant). Brief explanation of similarities
        
        Similar Movies/TV Shows (3-5 titles)
        - Title 1: Brief explanation of similarities
        - Title 2: Brief explanation of similarities
        - Title 3: Brief explanation of similarities
        - Title 4: Brief explanation of similarities (if relevant)
        - Title 5: Brief explanation of similarities (if relevant)

        Text to analyze:
        {text}
        
        Please ensure each section is clearly separated by blank lines and use consistent formatting with dashes for list items. Be brutally honest in the commercial viability assessment, highlighting both strengths and potential market challenges."""

        # Remove any whitespace from the API key
        clean_api_key = api_key.strip()
        
        # Try different auth header formats
        headers = {
            'Authorization': clean_api_key,  # Try direct key
            'Content-Type': 'application/json'
        }

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': [
                {'role': 'system', 'content': 'You are a literary expert skilled in analyzing query letters and manuscripts.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 2000
        }

        print("Making API request...")  # Debug print
        print(f"Base URL: {base_url}")  # Debug print
        print(f"Headers (auth type): {headers['Authorization'].split('-')[0] if headers.get('Authorization') else 'None'}")  # Debug print auth type only

        response = requests.post(
            f"{base_url.strip()}/chat/completions",
            headers=headers,
            json=data,
            timeout=30  # Add timeout
        )

        if response.status_code == 401:
            # Try alternative header format
            headers['Authorization'] = f'Bearer {clean_api_key}'
            print("Retrying with Bearer token...")  # Debug print
            response = requests.post(
                f"{base_url.strip()}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )

        if response.status_code == 401:
            print("Authentication error. Full response:", response.text)
            return """Error: Authentication failed. Please verify:
1. API key format is correct
2. API key has not expired
3. Base URL matches your API provider
Current error: {response.text}"""

        print(f"Response status: {response.status_code}")  # Debug print
        print(f"Response text: {response.text}")  # Debug print

        if response.status_code != 200:
            return f"Error code: {response.status_code} - {response.text}"

        response_data = response.json()
        return response_data['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error in analyze_text: {str(e)}")
        return f"Error analyzing text: {str(e)}"

@app.route('/analyze', methods=['POST'])
def analyze_input_text():
    if not request.is_json:
        return jsonify({'error': 'Request must be JSON'}), 400
        
    data = request.get_json()
    if 'text' not in data or not data['text'].strip():
        return jsonify({'error': 'No text provided'}), 400
    
    analysis = analyze_text(data['text'])
    
    if analysis.startswith('Error:'):
        return jsonify({'error': analysis}), 500
        
    return jsonify({
        'message': 'Text analyzed successfully!',
        'analysis': analysis
    })

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'query_letter' not in request.files:
            return jsonify({'error': 'No query letter uploaded'}), 400
            
        query_letter = request.files['query_letter']
        
        if query_letter.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        if query_letter:
            try:
                # Save the file
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], query_letter.filename)
                query_letter.save(filepath)
                
                # Read and analyze the content
                with open(filepath, 'r', encoding='utf-8') as file:
                    content = file.read()
                    analysis = analyze_text(content)
                    
                    if analysis.startswith('Error:'):
                        return jsonify({'error': analysis}), 500
                    
                    return jsonify({
                        'message': 'File uploaded and analyzed successfully!',
                        'analysis': analysis
                    })
            except Exception as e:
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
            
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
