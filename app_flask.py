from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import shutil
from llama_index.core import (
    VectorStoreIndex,
    SimpleDirectoryReader,
    Settings,
    StorageContext,
    load_index_from_storage
)
from llama_index.llms.gemini import Gemini
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import google.generativeai as genai
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from cloudinary_storage import CloudinaryStorage

# Load environment variables
load_dotenv()

# Configuration
DATA_DIR = "./data"
PERSIST_DIR = "./storage"
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'md'}

# Create directories
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(PERSIST_DIR, exist_ok=True)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global index variable
index = None

# Initialize Cloudinary storage
use_cloudinary = all([
    os.getenv('CLOUDINARY_CLOUD_NAME'),
    os.getenv('CLOUDINARY_API_KEY'),
    os.getenv('CLOUDINARY_API_SECRET')
])

if use_cloudinary:
    storage = CloudinaryStorage()
    print("✅ Using Cloudinary for file storage")
else:
    storage = None
    print("⚠️  Using local file storage (files will not persist on server restart)")

# Initialize LLM and embeddings
def init_settings():
    """Initialize LLM and embeddings"""
    embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL)
    Settings.embed_model = embed_model
    
    api_key = os.getenv("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
        llm = Gemini(model_name="models/gemini-2.5-flash", api_key=api_key)
        Settings.llm = llm
        return llm, embed_model
    return None, embed_model

llm, embed_model = init_settings()

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_files():
    """Get list of files (from Cloudinary or local directory)"""
    if use_cloudinary and storage:
        # Get files from Cloudinary
        cloud_files = storage.list_files()
        return [f['name'] for f in cloud_files]
    else:
        # Get files from local directory
        if not os.path.exists(DATA_DIR):
            return []
        return [f for f in os.listdir(DATA_DIR) if not f.startswith('.') and os.path.isfile(os.path.join(DATA_DIR, f))]

def build_index():
    """Build or load the index"""
    global index
    
    files = get_files()
    if not files:
        index = None
        return None
    
    # Try to load existing index
    if os.path.exists(PERSIST_DIR):
        try:
            storage_context = StorageContext.from_defaults(persist_dir=PERSIST_DIR)
            index = load_index_from_storage(storage_context)
            return index
        except:
            pass
    
    # Build new index
    if use_cloudinary and storage:
        # Download all files from Cloudinary to local temp directory
        storage.download_all_files(DATA_DIR)
    
    file_paths = [os.path.join(DATA_DIR, f) for f in files]
    documents = SimpleDirectoryReader(input_files=file_paths).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=PERSIST_DIR)
    return index

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
    """Upload files to the data directory"""
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    uploaded = []
    
    for file in files:
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            
            if use_cloudinary and storage:
                # Upload to Cloudinary
                try:
                    storage.upload_file(file, filename)
                    uploaded.append(filename)
                except Exception as e:
                    print(f"Cloudinary upload error: {e}")
            else:
                # Save locally
                file.save(os.path.join(DATA_DIR, filename))
                uploaded.append(filename)
    
    return jsonify({
        'message': f'Uploaded {len(uploaded)} file(s)',
        'files': uploaded
    })

@app.route('/files', methods=['GET'])
def list_files():
    """List all files in the data directory"""
    files = get_files()
    return jsonify({'files': files})

@app.route('/files/<filename>', methods=['DELETE'])
def delete_file(filename):
    """Delete a file from Cloudinary or local storage"""
    try:
        if use_cloudinary and storage:
            # Delete from Cloudinary
            storage.delete_file(filename)
        else:
            # Delete from local storage
            file_path = os.path.join(DATA_DIR, secure_filename(filename))
            if not os.path.exists(file_path):
                return jsonify({'error': 'File not found'}), 404
            os.remove(file_path)
        
        return jsonify({'message': f'Deleted {filename}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reindex', methods=['POST'])
def reindex():
    """Rebuild the index from current files"""
    global index
    
    # Delete old storage
    if os.path.exists(PERSIST_DIR):
        shutil.rmtree(PERSIST_DIR)
        os.makedirs(PERSIST_DIR)
    
    # Rebuild index
    files = get_files()
    if not files:
        index = None
        return jsonify({'message': 'No files to index', 'file_count': 0})
    
    try:
        file_paths = [os.path.join(DATA_DIR, f) for f in files]
        documents = SimpleDirectoryReader(input_files=file_paths).load_data()
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=PERSIST_DIR)
        
        return jsonify({
            'message': 'Index rebuilt successfully',
            'file_count': len(files),
            'document_count': len(documents)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with the documents"""
    global index
    
    data = request.json
    query = data.get('query', '')
    
    if not query:
        return jsonify({'error': 'No query provided'}), 400
    
    if not llm:
        return jsonify({'error': 'Gemini API key not configured'}), 500
    
    if index is None:
        # Try to build index
        index = build_index()
        if index is None:
            return jsonify({'error': 'No documents indexed. Please upload files and reindex.'}), 400
    
    try:
        # Special handling for "what is the content" queries
        if query.strip().lower().startswith("what is the content"):
            files = get_files()
            if files:
                file_paths = [os.path.join(DATA_DIR, f) for f in files]
                docs = SimpleDirectoryReader(input_files=file_paths).load_data()
                full_text = "\n\n---\n\n".join([doc.text for doc in docs])
                return jsonify({'response': full_text})
            else:
                return jsonify({'error': 'No documents available'}), 400
        
        # Regular query
        files = get_files()
        file_list = ", ".join(files)
        
        query_engine = index.as_query_engine(
            similarity_top_k=5,
            system_prompt=(
                f"You have access to {len(files)} document(s): {file_list}. "
                "You answer strictly using the provided context from these documents. "
                "If the answer is not in the documents, reply: "
                "'I cannot answer this based on the provided documents.'"
            )
        )
        response = query_engine.query(query)
        
        return jsonify({'response': str(response)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Build initial index if files exist
    build_index()
    
    # Run the app
    port = int(os.getenv('PORT', 5001))
    app.run(debug=False, host='0.0.0.0', port=port)
