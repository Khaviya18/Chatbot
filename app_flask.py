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
DATA_DIR = "./data"

# Create data directory if it doesn't exist
os.makedirs(DATA_DIR, exist_ok=True)

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

def normalize_query(query):
    """Normalize and enhance query understanding"""
    query_lower = query.strip().lower()
    
    # Common query variations mapping
    query_variations = {
        'academics': ['academics', 'academic', 'education', 'qualifications', 'degrees', 'studies', 'schooling'],
        'experience': ['experience', 'work', 'employment', 'job', 'career', 'professional experience'],
        'skills': ['skills', 'skill', 'abilities', 'competencies', 'expertise'],
        'name': ['name', 'person name', 'who is', 'person\'s name', 'candidate name'],
        'contact': ['contact', 'email', 'phone', 'address', 'location'],
        'projects': ['projects', 'project', 'work done', 'portfolio'],
    }
    
    # Enhance query with context
    enhanced_query = query
    
    # Add context for common question patterns
    if any(term in query_lower for term in ['academics', 'academic', 'education', 'qualification']):
        enhanced_query += " (Look for Education, Academics, Qualifications, Degrees, University, College, School sections)"
    elif any(term in query_lower for term in ['experience', 'work', 'employment', 'job']):
        enhanced_query += " (Look for Experience, Work History, Employment, Professional Experience sections)"
    elif any(term in query_lower for term in ['skill', 'ability', 'expertise']):
        enhanced_query += " (Look for Skills, Technical Skills, Competencies, Expertise sections)"
    
    return enhanced_query

def extract_text_from_file(file_content, filename):
    """Extract text from PDF or text file with improved extraction"""
    if not file_content:
        return ""
        
    ext = filename.rsplit('.', 1)[1].lower()
    
    if ext == 'pdf':
        try:
            pdf_reader = PdfReader(io.BytesIO(file_content))
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                if page_text:
                    # Clean up the text - remove excessive whitespace but keep structure
                    page_text = ' '.join(page_text.split())
                    text += page_text + "\n\n"
            
            # If extraction seems empty, try alternative method
            if not text.strip():
                print(f"Warning: PDF extraction returned empty text for {filename}, trying alternative method")
                text = ""
                for page in pdf_reader.pages:
                    try:
                        # Try extracting with layout preservation
                        page_text = page.extract_text(extraction_mode="layout")
                        if page_text:
                            text += page_text + "\n\n"
                    except:
                        pass
            
            return text.strip()
        except Exception as e:
            print(f"PDF extraction error for {filename}: {e}")
            return ""
    else:
        # For text files, decode with error handling
        try:
            return file_content.decode('utf-8', errors='ignore')
        except:
            try:
                return file_content.decode('latin-1', errors='ignore')
            except:
                return str(file_content)

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
    """Upload files to Cloudinary or local storage"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            try:
                if use_cloudinary and storage:
                    # Upload to Cloudinary
                    storage.upload_file(file, filename)
                    uploaded.append(filename)
                else:
                    # Save to local storage
                    file_path = os.path.join(DATA_DIR, filename)
                    file.save(file_path)
                    uploaded.append(filename)
                    print(f"✅ Saved {filename} to local storage")
            except Exception as e:
                print(f"Upload error: {e}")
    
    return jsonify({
        'message': f'Uploaded {len(uploaded)} file(s)',
        'files': uploaded
    })

@app.route('/files', methods=['GET'])
def list_files():
    """List all files from Cloudinary or local storage"""
    if use_cloudinary and storage:
        cloud_files = storage.list_files()
        files = [f['name'] for f in cloud_files]
    else:
        # List files from local storage
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) 
                    if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
        else:
            files = []
    
    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from Cloudinary or local storage"""
    try:
        if use_cloudinary and storage:
            storage.delete_file(filename)
        else:
            # Delete from local storage
            file_path = os.path.join(DATA_DIR, secure_filename(filename))
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"✅ Deleted {filename} from local storage")
            else:
                return jsonify({'error': 'File not found'}), 404
        
        return jsonify({'message': f'Deleted {filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reindex', methods=['POST'])
def reindex():
    """Reindex - just return success since we query on-demand"""
    if use_cloudinary and storage:
        files = storage.list_files()
        file_count = len(files)
    else:
        # Count local files
        if os.path.exists(DATA_DIR):
            files = [f for f in os.listdir(DATA_DIR) 
                    if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
            file_count = len(files)
        else:
            file_count = 0
    
    return jsonify({
        'message': 'Index refreshed',
        'file_count': file_count,
        'document_count': file_count
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with documents using Gemini"""
    if not model:
        return jsonify({'error': 'Gemini API not configured'}), 500
    
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    # Normalize and enhance the query
    enhanced_query = normalize_query(query)
    
    try:
        # Initialize variables
        cloud_files = None
        local_files = None
        file_list = ""
        all_text = ""
        file_count = 0
        
        # Get all files from Cloudinary or local storage
        if use_cloudinary and storage:
            cloud_files = storage.list_files()
            file_list = ", ".join([f['name'] for f in cloud_files])
            file_count = len(cloud_files)
            
            if not cloud_files:
                return jsonify({'error': 'No documents available. Please upload files first.'}), 400
            
            # Download and extract text from all files
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
                    if text and text.strip():
                        # Clean text: remove excessive whitespace but preserve paragraph structure
                        lines = text.split('\n')
                        cleaned_lines = []
                        prev_empty = False
                        
                        for line in lines:
                            stripped = line.strip()
                            if stripped:  # Non-empty line
                                cleaned_lines.append(stripped)
                                prev_empty = False
                            elif not prev_empty:  # First empty line in a sequence - keep it
                                cleaned_lines.append('')
                                prev_empty = True
                        
                        cleaned_text = '\n'.join(cleaned_lines)
                        all_text += f"\n\n{'='*60}\nDOCUMENT: {file_info['name']}\n{'='*60}\n{cleaned_text}\n"
                        print(f"✅ Extracted {len(cleaned_text)} characters from {file_info['name']}")
                    else:
                        print(f"⚠️ Warning: No text extracted from {file_info['name']} (extracted text length: {len(text) if text else 0})")
                except Exception as e:
                    print(f"❌ Error extracting text from {file_info['name']}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        else:
            # Use local storage
            if not os.path.exists(DATA_DIR):
                return jsonify({'error': 'No documents available. Please upload files first.'}), 400
            
            local_files = [f for f in os.listdir(DATA_DIR) 
                          if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
            file_list = ", ".join(local_files)
            file_count = len(local_files)
            
            if not local_files:
                return jsonify({'error': 'No documents available. Please upload files first.'}), 400
            
            for filename in local_files:
                file_path = os.path.join(DATA_DIR, filename)
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    text = extract_text_from_file(content, filename)
                    if text and text.strip():
                        # Clean text
                        lines = text.split('\n')
                        cleaned_lines = []
                        prev_empty = False
                        
                        for line in lines:
                            stripped = line.strip()
                            if stripped:
                                cleaned_lines.append(stripped)
                                prev_empty = False
                            elif not prev_empty:
                                cleaned_lines.append('')
                                prev_empty = True
                        
                        cleaned_text = '\n'.join(cleaned_lines)
                        all_text += f"\n\n{'='*60}\nDOCUMENT: {filename}\n{'='*60}\n{cleaned_text}\n"
                        print(f"✅ Extracted {len(cleaned_text)} characters from {filename}")
                    else:
                        print(f"⚠️ Warning: No text extracted from {filename}")
                except Exception as e:
                    print(f"❌ Error reading {filename}: {e}")
                    import traceback
                    traceback.print_exc()
                    continue
        
        # Special handling for "what is the content" queries
        query_lower = query.strip().lower()
        if any(phrase in query_lower for phrase in ["what is the content", "show me the content", "display the content", "full content", "what's in the pdf", "what's in the document"]):
            if all_text and all_text.strip():
                # Format the response nicely with clear structure
                formatted_response = f"📄 **Full Content of All Documents**\n\n{all_text}\n\n---\n*End of document content*"
                print(f"✅ Returning full content ({len(all_text)} characters)")
                return jsonify({'response': formatted_response})
            else:
                # If no text was extracted, provide helpful message and try to debug
                print(f"⚠️ Warning: all_text is empty. Files processed: {file_count}")
                error_msg = f"⚠️ **No text content could be extracted from the documents.**\n\n"
                error_msg += f"**Available files:** {file_list}\n\n"
                error_msg += "**Possible reasons:**\n"
                error_msg += "- Files may be empty or corrupted\n"
                error_msg += "- Files may be in an unsupported format\n"
                error_msg += "- Text extraction may have failed\n\n"
                error_msg += "**Please try:**\n"
                error_msg += "- Asking a specific question about the documents\n"
                error_msg += "- Re-uploading the files\n"
                error_msg += "- Checking if the files contain readable text"
                return jsonify({'response': error_msg})
        
        # Create a professional-grade prompt with advanced reasoning
        prompt = f"""You are an expert document analysis assistant with professional-grade accuracy. Your task is to answer questions based EXCLUSIVELY on the provided documents.

═══════════════════════════════════════════════════════════════
DOCUMENTS AVAILABLE ({file_count} file(s)):
{file_list}
═══════════════════════════════════════════════════════════════

DOCUMENT CONTENT:
{all_text}

═══════════════════════════════════════════════════════════════
USER QUESTION: {query}
ENHANCED UNDERSTANDING: {enhanced_query}
═══════════════════════════════════════════════════════════════

PROFESSIONAL ANALYSIS PROTOCOL:

STEP 1 - QUERY UNDERSTANDING:
- Parse the question carefully to understand what information is being requested
- Identify key entities: names, dates, skills, qualifications, experiences, achievements, etc.
- Recognize question variations: "academics" = "education" = "qualifications" = "academic background"
- Understand context: "here" = "in these documents", "the person" = "the subject of the document"

STEP 2 - COMPREHENSIVE SEARCH:
- Search through ALL document content systematically
- Look for exact matches AND semantic equivalents
- Check all sections: headers, body text, lists, tables, etc.
- For resumes/CVs, search: Education, Academics, Qualifications, Experience, Work History, Skills, Achievements, Projects, Certifications, etc.
- Consider alternative phrasings and synonyms

STEP 3 - INFORMATION EXTRACTION:
- Extract ALL relevant information, not just the first match
- Look for related context that might answer the question
- If asking about a category (like "academics"), find ALL items in that category
- If asking about a person, find their name in multiple places (header, signature, etc.)

STEP 4 - ANSWER FORMULATION:
- Provide complete, accurate answers based on the extracted information
- If multiple pieces of information exist, include all relevant details
- Format answers clearly and professionally
- Use bullet points or lists when appropriate
- Cite which document the information came from if multiple documents exist

STEP 5 - VERIFICATION:
- Double-check that your answer is supported by the document content
- Ensure you haven't missed any relevant information
- Verify the answer directly addresses the question asked

ANSWER GUIDELINES:
✅ DO:
- Answer based ONLY on information found in the documents
- Be thorough and comprehensive
- Provide complete information when available
- Use natural, professional language
- Include relevant details and context
- Handle question variations intelligently ("academics" = "education" = "qualifications")

❌ DON'T:
- Make up information not in the documents
- Say "I cannot answer" unless you've thoroughly searched and found nothing
- Skip information that's clearly present
- Give vague or incomplete answers when details are available

EXAMPLES OF GOOD ANSWERS:

Question: "What is the person's name?"
Good Answer: "The person's name is [Name] as mentioned in the document header and throughout the resume."

Question: "What is academics?" or "What is here academics?"
Good Answer: "Based on the Education/Academics section: [List all academic qualifications, degrees, institutions, dates, etc. found in the documents]"

Question: "What skills does the person have?"
Good Answer: "The person has the following skills: [List all skills found in Skills section, Experience section, etc.]"

═══════════════════════════════════════════════════════════════

Now, analyze the documents and provide a professional, comprehensive answer to the user's question.

ANSWER:"""
        
        # Professional generation configuration for accurate responses
        generation_config = {
            "temperature": 0.3,  # Lower temperature for more accurate, focused answers
            "top_p": 0.9,
            "top_k": 40,
            "max_output_tokens": 4096,  # Increased for comprehensive answers
        }
        
        # Use safety settings that allow more content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        response = model.generate_content(
            prompt,
            generation_config=generation_config,
            safety_settings=safety_settings
        )
        
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
