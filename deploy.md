# Quick Deployment Guide

## Heroku Deployment (Recommended)

### Prerequisites
1. Install [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)
2. Create a [Heroku account](https://signup.heroku.com/)

### Deployment Steps

```bash
# 1. Initialize Git (if not already done)
git init
git add .
git commit -m "Ready for deployment"

# 2. Login to Heroku
heroku login

# 3. Create Heroku app (choose a unique name)
heroku create evalumate-power-switch

# 4. Set environment variables
heroku config:set SECRET_KEY="$(openssl rand -base64 32)"
heroku config:set FLASK_ENV="production"

# 5. Deploy
git push heroku main

# 6. Open your app
heroku open
```

### Your app will be live at:
`https://evalumate-power-switch.herokuapp.com`

## Alternative: Railway

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "Deploy from GitHub repo"
4. Select your repository
5. Railway automatically detects and deploys Flask apps

## Alternative: Render

1. Go to [render.com](https://render.com)
2. Sign up and connect GitHub
3. Create "New Web Service"
4. Select your repository
5. Use these settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`

## Domain & SSL
All platforms provide:
- Free HTTPS/SSL certificates
- Custom domain support
- Automatic deployments from Git

## Monitoring
Your app includes:
- Error handling
- File cleanup
- Production-ready configuration
