from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from cloudinary_storage import CloudinaryStorage
from pypdf import PdfReader
import io

# Load environment variables
load_dotenv()

# Configuration
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize Cloudinary storage
# Option 1: Try environment variables first
cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
cloud_api_key = os.getenv('CLOUDINARY_API_KEY')
cloud_api_secret = os.getenv('CLOUDINARY_API_SECRET')

# Option 2: Fallback to hardcoded credentials (uncomment and fill in if needed)
# cloud_name = "your_cloudinary_cloud_name"
# cloud_api_key = "your_cloudinary_api_key"
# cloud_api_secret = "your_cloudinary_api_secret"

use_cloudinary = all([cloud_name, cloud_api_key, cloud_api_secret])

if use_cloudinary:
    storage = CloudinaryStorage(cloud_name=cloud_name, api_key=cloud_api_key, api_secret=cloud_api_secret)
    print("✅ Using Cloudinary for file storage")
else:
    storage = None
    print("⚠️  Cloudinary not configured")

# Initialize Gemini
# Option 1: Try environment variable first
api_key = os.getenv("GEMINI_API_KEY")

# Option 2: Fallback to hardcoded key
if not api_key:
    api_key = "AIzaSyAmw5XvDFTid3Bdocds7ZJDiAlJXJT5qmU"

if api_key:
    genai.configure(api_key=api_key)
    # Use stable 2.0 Flash model (verified available)
    model = genai.GenerativeModel('gemini-2.0-flash')
    print("✅ Gemini initialized")
else:
    model = None
    print("⚠️  Gemini API key not configured - please set GEMINI_API_KEY env var or hardcode it in app_flask.py")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(file_content, filename):
    """Extract text from PDF or text file"""
    if not file_content:
        return ""
        
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += (page.extract_text() or "") + "\n"
            return text
        except Exception as e:
            print(f"PDF extraction error for {filename}: {e}")
            return ""
    else:
        return file_content.decode('utf-8', errors='ignore')

# Routes
@app.route('/')
def serve_frontend():
    """Serve the main HTML page"""
    return send_from_directory('web', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('web', path)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload files to Cloudinary"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    if not use_cloudinary or not storage:
        return jsonify({'error': 'Cloud storage not configured'}), 500
    
    files = request.files.getlist('files')
    uploaded = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                storage.upload_file(file, filename)
                uploaded.append(filename)
            except Exception as e:
                print(f"Upload error: {e}")
    
    return jsonify({
        'message': f'Uploaded {len(uploaded)} file(s)',
        'files': uploaded
    })

@app.route('/files', methods=['GET'])
def list_files():
    """List all files"""
    if use_cloudinary and storage:
        cloud_files = storage.list_files()
        files = [f['name'] for f in cloud_files]
    else:
        files = []
    
    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file"""
    if not use_cloudinary or not storage:
        return jsonify({'error': 'Cloud storage not configured'}), 500
    
    try:
        storage.delete_file(filename)
        return jsonify({'message': f'Deleted {filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reindex', methods=['POST'])
def reindex():
    """Reindex - just return success since we query on-demand"""
    if use_cloudinary and storage:
        files = storage.list_files()
        return jsonify({
            'message': 'Index refreshed',
            'file_count': len(files),
            'document_count': len(files)
        })
    return jsonify({'message': 'No files', 'file_count': 0})

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with documents using Gemini"""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 500
    
    if not use_cloudinary or not storage:
        return jsonify({'error': 'Cloud storage not configured'}), 500
    
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        # Get all files from Cloudinary
        cloud_files = storage.list_files()
        
        if not cloud_files:
            return jsonify({'error': 'No documents available. Please upload files first.'}), 400
        
        # Download and extract text from all files
        all_text = ""
        for file_info in cloud_files:
            import requests
            print(f"Downloading {file_info['name']} from {file_info['url']}")
            response = requests.get(file_info['url'])
            
            if response.status_code != 200:
                print(f"Failed to download {file_info['name']}: Status {response.status_code}")
                continue
                
            content = response.content
            print(f"Downloaded {len(content)} bytes")
            
            if not content:
                print(f"Warning: Empty content for {file_info['name']}")
                continue
                
            try:
                text = extract_text_from_file(content, file_info['name'])
                all_text += f"\n\n=== {file_info['name']} ===\n{text}"
            except Exception as e:
                print(f"Error extracting text from {file_info['name']}: {e}")
                continue
        
        # Create prompt with context
        file_list = ", ".join([f['name'] for f in cloud_files])
        prompt = f"""You have access to {len(cloud_files)} document(s): {file_list}.

Here is the content of all documents:
{all_text}

User question: {query}

Answer strictly based on the provided documents. If the answer is not in the documents, say "I cannot answer this based on the provided documents." """
        
        # Query Gemini
        response = model.generate_content(prompt)
        
        return jsonify({'response': response.text})
    except Exception as e:
        error_msg = str(e)
        # Check for API key errors
        if '403' in error_msg or 'API key' in error_msg or 'leaked' in error_msg.lower():
            return jsonify({
                'error': 'API key error: Your Gemini API key is invalid or has been revoked. Please get a new key from https://aistudio.google.com/apikey and update your environment variables.'
            }), 403
        elif '401' in error_msg or 'unauthorized' in error_msg.lower():
            return jsonify({
                'error': 'Authentication failed: Please check your GEMINI_API_KEY environment variable.'
            }), 401
        else:
            return jsonify({'error': f'Error: {error_msg}'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
