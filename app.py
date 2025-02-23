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
import PyPDF2
import tiktoken
import io

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
        if db is None:
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
            db = get_db()
            error_msg = "Failed to save email. Database connected: " + str(db is not None)
            print(f"Error: {error_msg}")
            return jsonify({'success': False, 'message': error_msg}), 500
    except Exception as e:
        error_msg = f"Subscribe error: {str(e)}\nType: {type(e)}"
        print(error_msg)
        traceback.print_exc()
        # For debugging, return the actual error message
        return jsonify({'success': False, 'message': error_msg}), 500

def process_pdf(file):
    """Process PDF file and extract text"""
    try:
        # Read PDF file
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file.read()))
        text = ""
        
        # Extract text from all pages
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
            
        return text.strip()
    except Exception as e:
        print(f"Error processing PDF: {str(e)}")
        traceback.print_exc()
        raise

def split_text_into_chunks(text, max_tokens=3000):
    """Split text into chunks that won't exceed token limit"""
    encoding = tiktoken.encoding_for_model("gpt-4")
    tokens = encoding.encode(text)
    chunks = []
    current_chunk = []
    current_length = 0
    
    for token in tokens:
        if current_length >= max_tokens:
            chunks.append(encoding.decode(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(token)
        current_length += 1
    
    if current_chunk:
        chunks.append(encoding.decode(current_chunk))
    
    return chunks

def validate_and_fix_comps(analysis, time_range, session, api_key, base_url, org_id, headers):
    if time_range != 'recent':
        return analysis

    current_year = 2025  # Since we know the current year from metadata
    cutoff_year = current_year - 5

    validation_prompt = f"""You are a literary agent validating comparable titles. The following analysis contains titles that may be older than {cutoff_year}.
For each title, check its publication year. If any title was published before {cutoff_year}, provide a new comparable title published in {cutoff_year} or later that matches the same criteria.

Current analysis:
{analysis}

For any title published before {cutoff_year}, provide a replacement in this format:
REPLACE: [Old Title] ([Old Year])
WITH: [New Title] by [Author] ([Year]) - [2-3 sentences explaining why this is a good replacement]

If all titles are from {cutoff_year} or later, respond with: "All titles are within the 5-year range."

Remember:
1. Only suggest replacements for titles published before {cutoff_year}
2. All replacement titles must be published in {cutoff_year} or later
3. Maintain the same type of comparison (thematic, genre, voice, or trope) as the original
4. Ensure the replacement title is not already used elsewhere in the analysis
5. Include the publication year for each replacement title"""

    data = {
        'model': 'gpt-4',
        'messages': [
            {
                'role': 'system',
                'content': validation_prompt
            },
            {
                'role': 'user',
                'content': 'Please validate and provide replacements if needed.'
            }
        ],
        'temperature': 0.7,
        'max_tokens': 1000
    }

    try:
        response = session.post(
            f"{base_url}/v1/chat/completions",
            headers=headers,
            json=data,
            timeout=60
        )
        
        if response.status_code != 200:
            return analysis

        validation_result = response.json()['choices'][0]['message']['content']
        
        if "All titles are within the 5-year range" in validation_result:
            return analysis

        # Process replacements
        replacements = []
        for line in validation_result.split('\n'):
            if line.startswith('REPLACE:'):
                old_new = line.split('\nWITH:')
                if len(old_new) == 2:
                    old_title = old_new[0].replace('REPLACE:', '').strip()
                    new_title_full = old_new[1].strip()
                    replacements.append((old_title, new_title_full))

        # Apply replacements
        updated_analysis = analysis
        for old_title, new_title_full in replacements:
            # Extract just the title part from the old_title (before the year)
            old_title_clean = old_title.split('(')[0].strip()
            # Find and replace while preserving formatting
            updated_analysis = updated_analysis.replace(old_title_clean, new_title_full)

        return updated_analysis

    except Exception as e:
        print(f"Error in validation: {str(e)}")
        return analysis

def analyze_chunk(chunk, time_range, session):
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        org_id = os.getenv('OPENAI_ORG_ID')
        
        if not api_key or not base_url:
            raise Exception("API configuration missing")

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'User-Agent': 'ManuscriptAnalysis/1.0'
        }
        
        if org_id:
            headers['X-Organization-ID'] = org_id

        api_endpoint = f"{base_url}/v1/chat/completions"

        system_prompt = f"""You are a professional literary agent compiling a final manuscript analysis. 
Provide a concise analysis using EXACTLY this format with these EXACT headings:

PRIMARY COMPARABLE TITLES:
These are the three most similar overall matches to the manuscript{' published in the last 5 years (2020-2025)' if time_range == 'recent' else ''}:

1. [Title 1 by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
   - [2-3 sentences explaining overall similarities in multiple aspects]

2. [Title 2 by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
   - [2-3 sentences explaining overall similarities in multiple aspects]

3. [Title 3 by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
   - [2-3 sentences explaining overall similarities in multiple aspects]

THEMATIC COMPARABLE:
[Title by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
- [2-3 sentences focusing specifically on thematic similarities, even if the genre, style, or target audience differs]

GENRE COMPARABLE:
[Title by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
- [2-3 sentences focusing specifically on genre similarities and conventions, even if themes or style differs]

VOICE COMPARABLE:
[Title by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
- [2-3 sentences focusing specifically on writing style and narrative voice similarities, even if genre or themes differ]

TROPE COMPARABLE:
[Title by Author] ([Publication Year]) - {' Must be 2020 or later' if time_range == 'recent' else ''}
- [2-3 sentences focusing specifically on similar story tropes and plot devices, even if execution differs]

Note: Each title should be unique. If the best match for a category is already listed, use the next best match. 
Exclude any titles that are part of the same series or by the same author as the submitted manuscript.
{' All comparable titles must have been published in 2020 or later.' if time_range == 'recent' else ''}"""

        # Initial analysis
        for attempt in range(3):
            try:
                data = {
                    'model': 'gpt-4',
                    'messages': [
                        {
                            'role': 'system',
                            'content': system_prompt
                        },
                        {
                            'role': 'user',
                            'content': f"Analyze this manuscript chunk:\n\n{chunk}"
                        }
                    ],
                    'temperature': 0.7,
                    'max_tokens': 1000
                }

                response = session.post(
                    api_endpoint,
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                if response.status_code != 200:
                    error_message = f"API Error: {response.status_code}"
                    try:
                        error_data = response.json()
                        if 'error' in error_data:
                            error_message += f" - {error_data['error'].get('message', '')}"
                    except:
                        error_message += f" - {response.text}"
                    raise Exception(error_message)

                analysis = response.json()['choices'][0]['message']['content']
                
                # Validate and fix publication years if needed
                if time_range == 'recent':
                    analysis = validate_and_fix_comps(analysis, time_range, session, api_key, base_url, org_id, headers)
                
                return analysis

            except requests.exceptions.Timeout:
                if attempt == 2:
                    raise Exception("The analysis is taking longer than expected. Please try again with a shorter text.")
                continue
            except requests.exceptions.RequestException as e:
                if attempt == 2:
                    raise Exception(f"Error communicating with the analysis service: {str(e)}")
                continue

    except Exception as e:
        print(f"Error analyzing chunk: {str(e)}")
        traceback.print_exc()
        raise

def compile_analysis(chunk_analyses):
    """Compile all chunk analyses into a final comprehensive analysis"""
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        base_url = os.getenv('OPENAI_BASE_URL')
        org_id = os.getenv('OPENAI_ORG_ID')
        
        if not api_key or not base_url:
            raise Exception("API configuration missing")

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

        system_prompt = """You are a professional literary agent compiling a final manuscript analysis. 
Provide a concise analysis using EXACTLY this format with these EXACT headings:

PRIMARY COMPARABLE TITLES:
These are the three most similar overall matches to the manuscript:

1. [Title 1 by Author]
   - [2-3 sentences explaining overall similarities in multiple aspects]

2. [Title 2 by Author]
   - [2-3 sentences explaining overall similarities in multiple aspects]

3. [Title 3 by Author]
   - [2-3 sentences explaining overall similarities in multiple aspects]

THEMATIC COMPARABLE:
[Title by Author]
- [2-3 sentences focusing specifically on thematic similarities, even if the genre, style, or target audience differs]

GENRE COMPARABLE:
[Title by Author]
- [2-3 sentences focusing specifically on genre similarities and conventions, even if themes or style differs]

VOICE COMPARABLE:
[Title by Author]
- [2-3 sentences focusing specifically on writing style and narrative voice similarities, even if genre or themes differ]

TROPE COMPARABLE:
[Title by Author]
- [2-3 sentences focusing specifically on similar story tropes and plot devices, even if execution differs]

Note: Each title should be unique. If the best match for a category is already listed, use the next best match. Exclude any titles that are part of the same series or by the same author as the submitted manuscript.

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
- [Core demographic description]"""

        data = {
            'model': 'gpt-4',
            'messages': [
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': f"Based on these chunk analyses, provide a comprehensive manuscript analysis:\n\n{json.dumps(chunk_analyses, indent=2)}"
                }
            ],
            'temperature': 0.7,
            'max_tokens': 1500
        }

        response = session.post(
            api_endpoint,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code != 200:
            raise Exception(f"API Error: {response.status_code} - {response.text}")

        response_data = response.json()
        return response_data['choices'][0]['message']['content']

    except Exception as e:
        print(f"Error compiling analysis: {str(e)}")
        traceback.print_exc()
        raise

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        text = data.get('text', '')
        time_range = data.get('timeRange', 'all')

        if not text:
            return jsonify({'error': 'No text provided'}), 400

        analysis = analyze_text(text, time_range)
        return jsonify({'result': analysis})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400

        file = request.files['file']
        time_range = request.form.get('timeRange', 'all')

        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400

        if not file.filename.endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400

        # Read the PDF file
        pdf_text = process_pdf(file)
        
        if not pdf_text.strip():
            return jsonify({'error': 'Could not extract text from PDF'}), 400

        # Analyze the extracted text
        analysis = analyze_text(pdf_text, time_range)
        return jsonify({'result': analysis})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def analyze_text(text, time_range='all'):
    chunks = split_text_into_chunks(text)
    all_analyses = []

    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(
        max_retries=requests.urllib3.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504]
        )
    )
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    for chunk in chunks:
        try:
            analysis = analyze_chunk(chunk, time_range, session)
            all_analyses.append(analysis)
        except requests.exceptions.Timeout:
            raise Exception("The analysis is taking longer than expected. Please try again with a shorter text or try again later.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error communicating with the analysis service: {str(e)}")
        except Exception as e:
            raise Exception(f"An unexpected error occurred: {str(e)}")

    final_analysis = compile_analysis(all_analyses)
    return final_analysis

@app.route('/subscribers', methods=['GET'])
def get_subscribers():
    try:
        # Check if the request includes a secret key
        secret_key = request.args.get('key')
        if not secret_key or secret_key != os.getenv('ADMIN_KEY'):
            return jsonify({'error': 'Unauthorized'}), 401

        # Get fresh DB connection
        db = get_db()
        if db is None:
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
        if db is None:
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
