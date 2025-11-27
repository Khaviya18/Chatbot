# Quick Setup Guide

## Get Your New Gemini API Key

1. Go to: https://aistudio.google.com/apikey
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the new API key

## Hardcode Your API Key

Open `app_flask.py` and find this line (around line 40):

```python
api_key = "YOUR_NEW_GEMINI_API_KEY_HERE"  # Replace this with your new API key
```

Replace `YOUR_NEW_GEMINI_API_KEY_HERE` with your actual API key, like:

```python
api_key = "AIzaSy...your_actual_key_here..."
```

## Optional: Hardcode Cloudinary Credentials

If you want to use Cloudinary for file storage, uncomment and fill in these lines in `app_flask.py` (around line 28):

```python
cloud_name = "your_cloudinary_cloud_name"
cloud_api_key = "your_cloudinary_api_key"
cloud_api_secret = "your_cloudinary_api_secret"
```

## Run the App

```bash
python app_flask.py
```

Or if using the production setup:

```bash
gunicorn app_flask:app
```

That's it! Your credentials are now hardcoded and the app should work.

