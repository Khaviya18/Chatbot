# Security Guide

## ⚠️ Important Security Notes

### API Keys
- **NEVER** commit API keys or secrets to the repository
- Always use environment variables (`.env` file locally, platform environment variables in production)
- If you accidentally commit an API key:
  1. **Immediately revoke it** and generate a new one
  2. Remove it from git history (use `git filter-branch` or BFG Repo-Cleaner)
  3. Add it to `.gitignore` if not already there

### Current Status
- The `.env` file is already in `.gitignore` ✅
- All API keys should be stored in environment variables ✅

## Getting a New Gemini API Key

If your API key was leaked or revoked:

1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Sign in with your Google account
3. Click "Create API Key" or "Get API Key"
4. Copy the new API key
5. Add it to your `.env` file:
   ```bash
   GEMINI_API_KEY=your_new_api_key_here
   ```
6. For production (Railway/Render), add it in the platform's environment variables section

## Getting Cloudinary Credentials (Optional)

If you need cloud storage:

1. Sign up at [Cloudinary](https://cloudinary.com/users/register/free)
2. Go to Dashboard → Settings
3. Copy your credentials:
   - Cloud Name
   - API Key
   - API Secret
4. Add to `.env`:
   ```bash
   CLOUDINARY_CLOUD_NAME=your_cloud_name
   CLOUDINARY_API_KEY=your_api_key
   CLOUDINARY_API_SECRET=your_api_secret
   ```

## Best Practices

1. ✅ Use environment variables for all secrets
2. ✅ Never hardcode credentials in code or documentation
3. ✅ Rotate API keys regularly
4. ✅ Use different keys for development and production
5. ✅ Monitor API usage for suspicious activity



