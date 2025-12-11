from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from cloudinary_storage import CloudinaryStorage
from pypdf import PdfReader
import io
# Removed user memory imports - switching to RAG-only system
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
# Get API key from environment variable
api_key = os.getenv("GEMINI_API_KEY")

if api_key and api_key.strip() and api_key != "your_api_key_here":
    try:
        genai.configure(api_key=api_key)
        # Use stable 2.0 Flash model (verified available)
        model = genai.GenerativeModel('gemini-2.0-flash')
        print("✅ Gemini initialized")
    except Exception as e:
        print(f"⚠️  Error initializing Gemini: {e}")
        model = None
else:
    model = None
    print("⚠️  Gemini API key not configured - please set GEMINI_API_KEY in .env file")
    print("   Get a free API key from: https://aistudio.google.com/apikey")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_with_retry(model, prompt, generation_config, safety_settings, max_retries=3):
    """Generate content with retry logic for rate limit errors"""
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
                # Exponential backoff: wait 2^attempt seconds (2, 4, 8 seconds)
                wait_time = 2 ** attempt
                print(f"⚠️ Rate limit hit, retrying in {wait_time} seconds... (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
            else:
                return None, e
    
    return None, Exception("Max retries exceeded")

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
    """Extract text from PDF or text file with improved extraction and multiple fallback methods"""
    if not file_content:
        print(f"⚠️ Warning: Empty file content for {filename}")
        return ""
        
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    
    if ext == 'pdf':
        try:
            # Validate PDF file
            if len(file_content) < 100:  # PDFs should be at least 100 bytes
                print(f"⚠️ Warning: File {filename} seems too small to be a valid PDF")
                return ""
            
            pdf_reader = PdfReader(io.BytesIO(file_content))
            num_pages = len(pdf_reader.pages)
            print(f"📄 Processing PDF {filename} with {num_pages} page(s)")
            
            if num_pages == 0:
                print(f"⚠️ Warning: PDF {filename} has no pages")
                return ""
            
            # Method 1: Standard extraction
            text = ""
            for i, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        # Clean up the text - remove excessive whitespace but keep structure
                        cleaned = ' '.join(page_text.split())
                        text += cleaned + "\n\n"
                except Exception as e:
                    print(f"⚠️ Error extracting page {i+1} from {filename}: {e}")
                    continue
            
            # Method 2: If standard extraction failed or returned little text, try layout mode
            if not text.strip() or len(text.strip()) < 50:
                print(f"⚠️ Standard extraction returned little/no text for {filename}, trying layout mode...")
                layout_text = ""
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        # Try extracting with layout preservation
                        page_text = page.extract_text(extraction_mode="layout")
                        if page_text and page_text.strip():
                            cleaned = ' '.join(page_text.split())
                            layout_text += cleaned + "\n\n"
                    except Exception as e:
                        # Layout mode might not be supported, try alternative
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                cleaned = ' '.join(page_text.split())
                                layout_text += cleaned + "\n\n"
                        except:
                            pass
                
                # Use layout text if it's better than standard extraction
                if len(layout_text.strip()) > len(text.strip()):
                    text = layout_text
            
            # Method 3: If still no text, try extracting raw text
            if not text.strip():
                print(f"⚠️ Trying raw text extraction for {filename}...")
                for i, page in enumerate(pdf_reader.pages):
                    try:
                        # Try to get any text from the page
                        if hasattr(page, 'extract_text'):
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n\n"
                    except:
                        continue
            
            extracted_text = text.strip()
            if extracted_text:
                print(f"✅ Successfully extracted {len(extracted_text)} characters from {filename}")
            else:
                print(f"❌ Failed to extract text from {filename} - PDF may be image-based or corrupted")
            
            return extracted_text
            
        except Exception as e:
            print(f"❌ PDF extraction error for {filename}: {e}")
            import traceback
            traceback.print_exc()
            return ""
    else:
        # For text files, decode with error handling
        try:
            return file_content.decode('utf-8', errors='ignore')
        except:
            try:
                return file_content.decode('latin-1', errors='ignore')
            except:
                try:
                    return file_content.decode('cp1252', errors='ignore')
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
    try:
        if use_cloudinary and storage:
            files = storage.list_files()
            file_count = len(files) if files else 0
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
    except Exception as e:
        print(f"❌ Error in reindex: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': f'Reindex failed: {str(e)}'
        }), 500

@app.route('/chat', methods=['POST'])
def chat():
    """RAG-only Chat - answers questions ONLY from uploaded documents"""
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
        
        # Get all files from Cloudinary or local storage (optional - allow chat without documents)
        if use_cloudinary and storage:
            cloud_files = storage.list_files()
            file_list = ", ".join([f['name'] for f in cloud_files]) if cloud_files else ""
            file_count = len(cloud_files) if cloud_files else 0
        else:
            cloud_files = None
            file_list = ""
            file_count = 0
        
        # Only process documents if files exist (Cloudinary)
        if file_count > 0 and cloud_files:
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
            # Use local storage (optional - allow chat without documents)
            if os.path.exists(DATA_DIR):
                local_files = [f for f in os.listdir(DATA_DIR) 
                              if os.path.isfile(os.path.join(DATA_DIR, f)) and not f.startswith('.')]
                file_list = ", ".join(local_files) if local_files else ""
                file_count = len(local_files) if local_files else 0
            else:
                local_files = []
                file_list = ""
                file_count = 0
        
        # Process local files if they exist
        if file_count > 0 and local_files:
            for filename in local_files:
                file_path = os.path.join(DATA_DIR, filename)
                try:
                    # Validate file exists and is readable
                    if not os.path.exists(file_path):
                        print(f"⚠️ Warning: File {filename} does not exist at {file_path}")
                        continue
                    
                    if not os.path.isfile(file_path):
                        print(f"⚠️ Warning: {filename} is not a regular file")
                        continue
                    
                    # Check file size
                    file_size = os.path.getsize(file_path)
                    if file_size == 0:
                        print(f"⚠️ Warning: File {filename} is empty")
                        continue
                    
                    if file_size > 50 * 1024 * 1024:  # 50MB limit
                        print(f"⚠️ Warning: File {filename} is too large ({file_size} bytes), skipping")
                        continue
                    
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    if not content:
                        print(f"⚠️ Warning: Could not read content from {filename}")
                        continue
                    
                    text = extract_text_from_file(content, filename)
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
                        all_text += f"\n\n{'='*60}\nDOCUMENT: {filename}\n{'='*60}\n{cleaned_text}\n"
                        print(f"✅ Extracted {len(cleaned_text)} characters from {filename}")
                    else:
                        print(f"⚠️ Warning: No text extracted from {filename} - file may be image-based, corrupted, or empty")
                except PermissionError as e:
                    print(f"❌ Permission error reading {filename}: {e}")
                    continue
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
        
        # Check if there are any documents available
        if not all_text or not all_text.strip() or file_count == 0:
            return jsonify({
                'error': 'No documents available. Please upload documents first before asking questions.'
            }), 400
        
        # Create RAG-only prompt - strictly document-based
        prompt = f"""You are a document analysis assistant. You answer questions ONLY from the provided documents.

═══════════════════════════════════════════════════════════════
DOCUMENTS AVAILABLE ({file_count} file(s)):
{file_list}
═══════════════════════════════════════════════════════════════

DOCUMENT CONTENT:
{all_text}

═══════════════════════════════════════════════════════════════
USER QUESTION: {query}
═══════════════════════════════════════════════════════════════

CRITICAL INSTRUCTIONS:
1. Answer ONLY using information from the documents above
2. If the information is not in the documents, respond: "I cannot find this information in the provided documents."
3. Do not use any external knowledge or make assumptions
4. Be precise and reference the document content when answering
5. If multiple documents are available, specify which document contains the answer

ANSWER:"""
        
        # RAG-focused generation configuration
        generation_config = {
            "temperature": 0.3,  # Lower temperature for more accurate, document-based responses
            "top_p": 0.8,
            "top_k": 20,
            "max_output_tokens": 2048,
        }
        
        # Use safety settings that allow more content
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
        
        try:
            # Use retry logic for rate limit errors
            response, api_error = generate_with_retry(
                model, prompt, generation_config, safety_settings, max_retries=3
            )
            
            if api_error:
                raise api_error
            
            # Check if response was blocked or has errors
            if not response or not hasattr(response, 'text'):
                error_msg = "The AI response was blocked or empty. This might be due to content filters or API issues."
                print(f"❌ Error: {error_msg}")
                return jsonify({'error': error_msg}), 500
            
            # Handle potential blocking reasons
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                    print(f"⚠️ Response blocked: {response.prompt_feedback.block_reason}")
                    return jsonify({
                        'error': f'Response was blocked: {response.prompt_feedback.block_reason}. Please try rephrasing your question.'
                    }), 400
            
            assistant_response = response.text
            
            if not assistant_response or not assistant_response.strip():
                error_msg = "The AI returned an empty response. Please try again."
                print(f"❌ Error: {error_msg}")
                return jsonify({'error': error_msg}), 500
                
        except Exception as api_error:
            error_msg = str(api_error)
            print(f"❌ Gemini API error: {error_msg}")
            import traceback
            traceback.print_exc()
            
            # Provide user-friendly error messages
            # Check for quota exceeded first (before invalid key check)
            if '429' in error_msg or 'quota' in error_msg.lower() or 'quota exceeded' in error_msg.lower() or 'rate limit' in error_msg.lower():
                # Extract retry delay if available
                retry_delay = "a few minutes"
                if 'retry in' in error_msg.lower() or 'retry_delay' in error_msg.lower():
                    import re
                    delay_match = re.search(r'retry in ([\d.]+)s', error_msg.lower())
                    if delay_match:
                        seconds = float(delay_match.group(1))
                        if seconds < 60:
                            retry_delay = f"{int(seconds)} seconds"
                        else:
                            retry_delay = f"{int(seconds/60)} minutes"
                
                return jsonify({
                    'error': f'Quota exceeded: The free tier API quota has been reached. Please wait {retry_delay} before trying again. Free tier has limited requests per day. Check your quota at https://aistudio.google.com/apikey or consider upgrading your plan.'
    
    # RAG-focused generation configuration
    generation_config = {
        "temperature": 0.3,  # Lower temperature for more accurate, document-based responses
        "top_p": 0.8,
        "top_k": 20,
        "max_output_tokens": 2048,
    }
    
    # Use safety settings that allow more content
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    try:
        # Use retry logic for rate limit errors
        response, api_error = generate_with_retry(
            model, prompt, generation_config, safety_settings, max_retries=3
        )
        
        if api_error:
            raise api_error
        
        # Check if response was blocked or has errors
        if not response or not hasattr(response, 'text'):
            error_msg = "The AI response was blocked or empty. This might be due to content filters or API issues."
            print(f"❌ Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
        
        # Handle potential blocking reasons
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
            if hasattr(response.prompt_feedback, 'block_reason') and response.prompt_feedback.block_reason:
                print(f"⚠️ Response blocked: {response.prompt_feedback.block_reason}")
                return jsonify({
                    'error': f'Response was blocked: {response.prompt_feedback.block_reason}. Please try rephrasing your question.'
                }), 400
        
        assistant_response = response.text
        
        if not assistant_response or not assistant_response.strip():
            error_msg = "The AI returned an empty response. Please try again."
            print(f"❌ Error: {error_msg}")
            return jsonify({'error': error_msg}), 500
            
    except Exception as api_error:
        error_msg = str(api_error)
        print(f"❌ Gemini API error: {error_msg}")
        import traceback
        traceback.print_exc()
        
        # Provide user-friendly error messages
        # Check for quota exceeded first (before invalid key check)
        if '429' in error_msg or 'quota' in error_msg.lower() or 'quota exceeded' in error_msg.lower() or 'rate limit' in error_msg.lower():
            # Extract retry delay if available
            retry_delay = "a few minutes"
            if 'retry in' in error_msg.lower() or 'retry_delay' in error_msg.lower():
                import re
                delay_match = re.search(r'retry in ([\d.]+)s', error_msg.lower())
                if delay_match:
                    seconds = float(delay_match.group(1))
                    if seconds < 60:
                        retry_delay = f"{int(seconds)} seconds"
                    else:
                        retry_delay = f"{int(seconds/60)} minutes"
            
            return jsonify({
                'error': f'Quota exceeded: The free tier API quota has been reached. Please wait {retry_delay} before trying again. Free tier has limited requests per day. Check your quota at https://aistudio.google.com/apikey or consider upgrading your plan.'
            }), 429
        elif '403' in error_msg and ('API key' in error_msg or 'invalid' in error_msg.lower() or 'revoked' in error_msg.lower()):
            return jsonify({
                'error': 'API key error: Your Gemini API key is invalid or has been revoked. Please get a new key from https://aistudio.google.com/apikey and update your environment variables.'
            }), 403
        elif '401' in error_msg or 'unauthorized' in error_msg.lower():
            return jsonify({
                'error': 'Authentication failed: Please check your GEMINI_API_KEY environment variable.'
            }), 401
        else:
            return jsonify({
                'error': f'Error generating response: {error_msg}. Please try again or rephrase your question.'
            }), 500
    
    # Return the response without saving conversation history
    return jsonify({'response': assistant_response})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
