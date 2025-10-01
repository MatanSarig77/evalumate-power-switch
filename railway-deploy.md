# Railway Deployment (No Credit Card Required!)

## Quick Railway Deployment

1. **Go to [railway.app](https://railway.app)**
2. **Sign up with GitHub** (free)
3. **Click "Deploy from GitHub repo"**
4. **Select your power_switch repository**
5. **Railway automatically detects Flask and deploys!**

## Why Railway?
- ✅ No credit card required
- ✅ Automatic HTTPS
- ✅ Auto-deploys from Git
- ✅ Free tier: 500 hours/month
- ✅ Custom domains available
- ✅ Faster than Heroku

## Alternative: Render
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Create "New Web Service"
4. Select your repository
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

Both are easier than Heroku and don't require credit cards!
