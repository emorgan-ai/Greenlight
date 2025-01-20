from flask import Flask, request, render_template, jsonify
import os
import requests
from dotenv import load_dotenv
import sys
import json
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Debug prints for environment setup
print("Environment Setup:")
print(f"OPENAI_API_KEY exists: {bool(os.getenv('OPENAI_API_KEY'))}")
print(f"OPENAI_BASE_URL exists: {bool(os.getenv('OPENAI_BASE_URL'))}")
print(f"OPENAI_ORG_ID exists: {bool(os.getenv('OPENAI_ORG_ID'))}")

app = Flask(__name__)

def save_email(email):
    try:
        # In a production environment, you should use a proper database
        # For now, we'll just return success without actually saving
        return True
    except Exception as e:
        print(f"Error saving email: {e}")
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/subscribe', methods=['POST'])
def subscribe():
    try:
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
    except Exception as e:
        print(f"Subscribe error: {str(e)}")
        return jsonify({'success': False, 'message': 'Server error'}), 500

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
        response = session.post(
            api_endpoint,
            headers=headers,
            json=data,
            timeout=8
        )
        print(f"Response status code: {response.status_code}")

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
            print(error_msg)
            return {"error": error_msg}

        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            result = response_data['choices'][0]['message']['content']
            print("API Response:", result)  # Debug log
            return {"result": result}
        else:
            print(f"Unexpected response format: {json.dumps(response_data, indent=2)}")
            return {"error": "Unexpected response format from API"}

    except requests.exceptions.Timeout:
        error_msg = "Request timed out. Please try again with a shorter text."
        print(error_msg)
        return {"error": error_msg}
    except requests.exceptions.RequestException as e:
        error_msg = f"Request error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}
    except Exception as e:
        error_msg = f"Server error: {str(e)}"
        print(error_msg)
        return {"error": error_msg}

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        result = analyze_text(data['text'])
        if 'error' in result:
            return jsonify(result), 500
        
        print(f"Analysis completed successfully")
        return jsonify(result)
    except Exception as e:
        error_msg = f"Analysis error: {str(e)}"
        print(error_msg)
        return jsonify({'error': error_msg}), 500

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
            error_msg = f"Upload error: {str(e)}"
            print(error_msg)
            return jsonify({'error': error_msg}), 500
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True, port=9000)
