# Document Chatbot - Deployment Instructions

## 🚀 Deploy to Render.com (Recommended)

### Step 1: Push to GitHub

```bash
git add .
git commit -m "Add deployment configuration"
git push origin main
```

### Step 2: Deploy on Render

1. Go to [https://render.com](https://render.com)
2. Sign up or login with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository: `Khaviya18/Chatbot`
5. Render will auto-detect the `render.yaml` configuration
6. Add environment variable:
   - Key: `GEMINI_API_KEY`
   - Value: Your Gemini API key
7. Click **"Create Web Service"**

**That's it!** Your app will be live at `https://your-app-name.onrender.com`

---

## 🚂 Alternative: Deploy to Railway

### Steps:

1. Push to GitHub (same as above)
2. Go to [https://railway.app](https://railway.app)
3. Sign up with GitHub
4. Click **"New Project"** → **"Deploy from GitHub repo"**
5. Select your repository
6. Add environment variable: `GEMINI_API_KEY`
7. Railway will auto-deploy

**Done!** Your app will be live with a Railway URL.

---

## 📝 Environment Variables

Make sure to set these on your hosting platform:

| Variable | Value | Required |
|----------|-------|----------|
| `GEMINI_API_KEY` | Your Gemini API key | Yes |
| `PORT` | Auto-set by platform | No (auto) |

---

## ⚠️ Important Notes

### File Storage
- **Current setup**: Files are stored locally in `./data` directory
- **Problem**: Files will be deleted when the server restarts on free hosting
- **Solution**: Use cloud storage (see below)

### Cloud Storage Options

#### Option 1: Cloudinary (Recommended)
- 25GB free storage
- Easy to integrate
- Reliable

#### Option 2: Supabase Storage
- 1GB free
- Includes database
- Good for small projects

**Need help integrating cloud storage?** Let me know!

---

## 🔍 Verify Deployment

After deployment:

1. Visit your app URL
2. Upload a test document
3. Click "Reindex"
4. Ask a question
5. Verify the response

---

## 🐛 Troubleshooting

### Build fails
- Check that `requirements-prod.txt` is in the repository
- Verify Python version (3.11)

### App crashes
- Check logs on Render/Railway dashboard
- Verify `GEMINI_API_KEY` is set correctly

### Files not persisting
- This is expected with local storage on free hosting
- Integrate cloud storage (Cloudinary/Supabase)

---

## 📦 Files Created for Deployment

- ✅ `render.yaml` - Render configuration
- ✅ `requirements-prod.txt` - Production dependencies with Gunicorn
- ✅ `Procfile` - Railway/Heroku configuration
- ✅ `.gitignore` - Updated to ignore sensitive files
- ✅ `app_flask.py` - Updated to use PORT environment variable

---

## 🎉 You're Ready!

Just run:

```bash
git add .
git commit -m "Ready for production deployment"
git push origin main
```

Then deploy on Render.com or Railway!
