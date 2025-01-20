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
    api_key = os.getenv('OPENAI_API_KEY')
    base_url = os.getenv('OPENAI_BASE_URL')
    
    if not api_key:
        return "Error: API key not set. Please add your API key to the .env file."
    if not base_url:
        return "Error: API base URL not set. Please add the base URL to the .env file."

    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ManuscriptAnalysis/1.0',
            'X-Organization-ID': os.getenv('OPENAI_ORG_ID', '')
        }

        # Create a session
        session = requests.Session()

        # Construct the full API endpoint
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

        print(f"\nAttempting connection to: {api_endpoint}")
        print(f"Headers being sent: {headers}")
        print(f"Request data: {json.dumps(data, indent=2)}")

        # First try a GET request to test connectivity
        try:
            print("\nTesting connection with GET request...")
            test_response = session.get(base_url)
            print(f"GET test response status: {test_response.status_code}")
            print(f"GET test response headers: {dict(test_response.headers)}")
            print(f"GET test response text: {test_response.text[:200]}")
        except Exception as e:
            print(f"GET test failed: {str(e)}")
            print(f"GET test error type: {type(e)}")

        print("\nSending main POST request...")
        response = session.post(
            api_endpoint,
            headers=headers,
            json=data,
            timeout=30
        )

        print(f"\nResponse status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Raw response text: {response.text[:1000]}")

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
            return error_msg

        try:
            response_data = response.json()
            if 'choices' in response_data and len(response_data['choices']) > 0:
                return response_data['choices'][0]['message']['content']
            else:
                print(f"Unexpected response format: {json.dumps(response_data, indent=2)}")
                return "Error: Unexpected response format from API"
        except json.JSONDecodeError as e:
            print(f"\nFailed to parse JSON response")
            print(f"Response content type: {response.headers.get('content-type', 'unknown')}")
            print(f"Full response text: {response.text}")
            return f"Error: Could not parse API response - {str(e)}"

    except requests.exceptions.SSLError as e:
        print(f"\nSSL Error: {str(e)}")
        print(f"SSL Error type: {type(e)}")
        return f"Error: SSL verification failed - {str(e)}"
    except requests.exceptions.ConnectionError as e:
        print(f"\nConnection error: {str(e)}")
        print(f"Connection error type: {type(e)}")
        return f"Error: Could not connect to API server - {str(e)}"
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        print(f"Error type: {type(e)}")
        return f"Error: {str(e)}"

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

@app.route('/upload', methods=['GET', 'POST'])
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
    print("\nStarting server on port 9000...")
    app.run(debug=True, port=9000)
