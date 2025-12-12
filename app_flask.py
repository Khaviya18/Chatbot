from flask import Flask, request, jsonify, send_from_directory, session, Response
from flask_cors import CORS
import os
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from cloudinary_storage import CloudinaryStorage
from pypdf import PdfReader
import io
import json
import re
import time

# Load environment variables
load_dotenv()

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}
DATA_DIR = "./data"

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app)

# Initialize Cloudinary storage
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
cloud_api_key = os.getenv('CLOUDINARY_API_KEY')
cloud_api_secret = os.getenv('CLOUDINARY_API_SECRET')

use_cloudinary = all([cloud_name, cloud_api_key, cloud_api_secret])

if use_cloudinary:
    storage = CloudinaryStorage(cloud_name=cloud_name, api_key=cloud_api_key, api_secret=cloud_api_secret)
    print("✅ Using Cloudinary for file storage")
else:
    storage = None
    print("⚠️  Cloudinary not configured")

# Initialize Gemini
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

if api_key and api_key.strip() and api_key != "your_api_key_here":
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        print(f"✅ Gemini initialized with model: {model_name}")
    except Exception as e:
        print(f"⚠️  Error initializing Gemini: {e}")
        model = None
else:
    model = None
    print("⚠️  Gemini API key not configured - please set GEMINI_API_KEY in .env file")
    print("   Get a free API key from: https://aistudio.google.com/apikey")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_with_retry(model, prompt, generation_config, safety_settings, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            return response, None
        except Exception as e:
            error_msg = str(e)
            is_rate_limit = '429' in error_msg or 'quota' in error_msg.lower() or 'rate limit' in error_msg.lower()
            if is_rate_limit and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"⚠️ Rate limit hit, retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return None, e
    return None, Exception("Max retries exceeded")

def normalize_query(query):
    return query.strip().lower()

def extract_text_from_file(file_content, filename):
    if not file_content:
        return ""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    if ext == 'pdf':
        try:
            if len(file_content) < 100:
                return ""
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                except:
                    continue
            return text.strip()
        except Exception as e:
            print(f"❌ PDF extraction error for {filename}: {e}")
            return ""
    else:
        try:
            return file_content.decode('utf-8', errors='ignore')
        except:
            return str(file_content)

@app.route('/')
def serve_frontend():
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('web', path)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    files = request.files.getlist('files')
    uploaded = []
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                if use_cloudinary and storage:
                    storage.upload_file(file, filename)
                    uploaded.append(filename)
                else:
                    file_path = os.path.join(DATA_DIR, filename)
                    file.save(file_path)
                    uploaded.append(filename)
            except Exception as e:
                print(f"Upload error: {e}")
    return jsonify({'message': f'Uploaded {len(uploaded)} file(s)', 'files': uploaded})

@app.route('/files', methods=['GET'])
def list_files():
    if use_cloudinary and storage:
        files = [f['name'] for f in storage.list_files()]
    else:
        files = []
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) 
                    if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    try:
        if use_cloudinary and storage:
            storage.delete_file(filename)
        else:
            file_path = os.path.join(DATA_DIR, secure_filename(filename))
            if os.path.exists(file_path):
                os.remove(file_path)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'message': f'Deleted {filename}'})

@app.route('/reindex', methods=['POST'])
def reindex():
    # Count actual files
    file_count = 0
    if os.path.exists(DATA_DIR):
        files = [f for f in os.listdir(DATA_DIR) 
                if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
        file_count = len(files)
    
    return jsonify({'message': f'Indexed {file_count} file(s)', 'file_count': file_count, 'document_count': file_count})

@app.route('/clear-session', methods=['POST'])
def clear_session():
    """Clear session and delete all local files"""
    try:
        # Delete local files
        if os.path.exists(DATA_DIR):
            for filename in os.listdir(DATA_DIR):
                file_path = os.path.join(DATA_DIR, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except:
                        pass
        session.clear()
        print("✅ Session cleared")
        return '', 200
    except Exception as e:
        print(f"Error clearing session: {e}")
        return '', 500

@app.route('/chat', methods=['POST'])
def chat():
    """Streaming RAG Endpoint"""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 500
    
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    def generate():
        try:
            # 1. Fetch current file list
            local_files = []
            if os.path.exists(DATA_DIR):
                local_files = [f for f in os.listdir(DATA_DIR) 
                              if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
            
            file_count = len(local_files)
            file_list = ", ".join(local_files)
            
            # 2. Extract text fresh
            all_text = ""
            if file_count > 0:
                for filename in local_files:
                    try:
                        with open(os.path.join(DATA_DIR, filename), 'rb') as f:
                            content = f.read()
                        text = extract_text_from_file(content, filename)
                        if text and text.strip():
                             all_text += f"\n\n{'='*60}\nDOCUMENT: {filename}\n{'='*60}\n{text}\n"
                    except Exception as e:
                        print(f"Error reading {filename}: {e}")
            
            # 3. Strict Check
            if not all_text.strip():
                yield f"data: {json.dumps({'content': 'I cannot answer this question because there are no documents uploaded. Please upload relevant documents first.', 'done': True})}\n\n"
                return
                
            # 4. Strict Prompt
            prompt = f"""You are a strict document analysis assistant.
            
            CRITICAL INSTRUCTIONS:
            1. Answer ONLY using the information provided in the documents below.
            2. If the answer is not explicitly in the documents, you MUST state: "I cannot find this information in the provided documents."
            3. Do NOT use outside knowledge, general facts, or assumptions.
            
            DOCUMENTS ({file_count} file(s)):
            {file_list}
            
            CONTENT:
            {all_text}
            
            USER QUESTION: {query}
            
            ANSWER:"""
            
            generation_config = {"temperature": 0.0, "max_output_tokens": 2048}
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            
            # Stream the response
            response = model.generate_content(
                prompt, 
                generation_config=generation_config, 
                safety_settings=safety_settings,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield f"data: {json.dumps({'content': chunk.text})}\n\n"
            
            # Send done signal
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            print(f"Chat error: {e}")
            yield f"data: {json.dumps({'error': str(e), 'done': True})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
