from flask import Flask, request, render_template, jsonify
import os
import json
import requests
from dotenv import load_dotenv

# Get the directory containing the script
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Look for .env file
env_path = os.path.join(script_dir, '.env')
print(f"Looking for .env file in: {env_path}")
load_dotenv(env_path)

app = Flask(__name__, 
           template_folder=os.path.join(script_dir, 'templates'),
           static_folder=os.path.join(script_dir, 'static'))

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

        session = requests.Session()
        api_endpoint = f"{base_url}/v1/chat/completions"

        data = {
            'model': 'gpt-4',
            'messages': [
                {'role': 'system', 'content': 'You are a professional literary agent and publishing expert.'},
                {'role': 'user', 'content': f'''Analyze the following query letter or excerpt and provide a detailed analysis in the following format:

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
        '''}
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
            return error_msg

        response_data = response.json()
        if 'choices' in response_data and len(response_data['choices']) > 0:
            return response_data['choices'][0]['message']['content']
        else:
            return "Error: Unexpected response format from API"

    except Exception as e:
        return f"Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.get_json()
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    result = analyze_text(data['text'])
    return jsonify({'result': result})
