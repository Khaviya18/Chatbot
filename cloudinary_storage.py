import cloudinary
import cloudinary.uploader
import cloudinary.api
import os
import tempfile
from werkzeug.utils import secure_filename

class CloudinaryStorage:
    """Handle file storage with Cloudinary"""
    
    def __init__(self, cloud_name=None, api_key=None, api_secret=None):
        """Initialize Cloudinary with credentials from parameters or environment"""
        cloud_name = cloud_name or os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = api_key or os.getenv('CLOUDINARY_API_KEY')
        api_secret = api_secret or os.getenv('CLOUDINARY_API_SECRET')
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        self.folder = 'chatbot_documents'
    
    def upload_file(self, file, filename):
        """
        Upload a file to Cloudinary
        Returns: URL of uploaded file
        """
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(
                file,
                folder=self.folder,
                resource_type='raw',  # For non-image files
                public_id=secure_filename(filename)
            )
            return result['secure_url']
        except Exception as e:
            raise Exception(f"Cloudinary upload failed: {str(e)}")
    
    def list_files(self):
        """
        List all files in Cloudinary folder
        Returns: List of file info dicts with 'name' and 'url'
        """
        try:
            result = cloudinary.api.resources(
                type='upload',
                prefix=self.folder,
                resource_type='raw',
                max_results=500
            )
            
            files = []
            for resource in result.get('resources', []):
                # Extract filename from public_id
                public_id = resource['public_id']
                filename = public_id.split('/')[-1]
                files.append({
                    'name': filename,
                    'url': resource['secure_url'],
                    'public_id': public_id
                })
            
            return files
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def delete_file(self, filename):
        """
        Delete a file from Cloudinary
        """
        try:
            public_id = f"{self.folder}/{secure_filename(filename)}"
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type='raw'
            )
            return result.get('result') == 'ok'
        except Exception as e:
            raise Exception(f"Cloudinary delete failed: {str(e)}")
    
    def download_file(self, url, local_path):
        """
        Download a file from Cloudinary URL to local path
        """
        import requests
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return True
        except Exception as e:
            raise Exception(f"Download failed: {str(e)}")
    
    def download_all_files(self, local_dir):
        """
        Download all files from Cloudinary to local directory
        Returns: List of local file paths
        """
        os.makedirs(local_dir, exist_ok=True)
        files = self.list_files()
        local_paths = []
        
        for file_info in files:
            local_path = os.path.join(local_dir, file_info['name'])
            self.download_file(file_info['url'], local_path)
            local_paths.append(local_path)
        
        return local_paths
