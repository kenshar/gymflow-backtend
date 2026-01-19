# GymFlow Backend Deployment Guide

## Deploy to Render

### Option 1: Automatic Deployment (Recommended)

1. **Go to Render Dashboard**
   - Visit [dashboard.render.com](https://dashboard.render.com)
   - Log in with your account

2. **Create New Web Service**
   - Click "New +" button
   - Select "Web Service"
   - Connect your GitHub repository: `kenshar/gymflow-backtend`

3. **Configure Service**
   - **Name**: `gymflow-backend-1`
   - **Region**: Oregon (US West) - matches your database
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT`

4. **Environment Variables**
   Add these in the Render dashboard:
   ```
   DATABASE_URL=postgresql://gymflow_user:wHYT8xecEougv94WYY2Vrc283adTXKQS@dpg-d5mu9275r7bs73dd4fb0-a.oregon-postgres.render.com/gymflow_20os

   FLASK_ENV=production
   SECRET_KEY=<generate-a-random-secret>
   JWT_ALGORITHM=HS256
   JWT_EXPIRY_MINUTES=30
   FRONTEND_URL=https://kenshar.github.io
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete (~5 minutes)
   - Your backend will be available at: `https://gymflow-backend-1.onrender.com`

### Option 2: Using render.yaml (Blueprint)

1. In Render Dashboard, click "New +" → "Blueprint"
2. Connect your `kenshar/gymflow-backtend` repository
3. Select the `render.yaml` file
4. Render will automatically create the web service and database
5. Update the DATABASE_URL in environment variables

## Verify Deployment

1. **Test Health Endpoint**
   ```bash
   curl https://gymflow-backend-1.onrender.com/
   ```
   Should return: `{"status": "Backend is running", "message": "GymFlow API is online"}`

2. **Test API Endpoint**
   ```bash
   curl https://gymflow-backend-1.onrender.com/api
   ```
   Should return: `{"message": "GymFlow API", "version": "1.0"}`

3. **Test Member Creation**
   ```bash
   curl -X POST https://gymflow-backend-1.onrender.com/api/admin/members/create \
     -H "Content-Type: application/json" \
     -d '{"name":"Test User","email":"test@example.com","phone":"+254123456789","membership":"Essential Fitness","startDate":"2026-01-20","endDate":"2026-02-20"}'
   ```

## Update Frontend

After backend is deployed, update the frontend to use the production backend:

1. **Edit `.env.production`** in `gymflow-frontend`:
   ```
   VITE_API_URL=https://gymflow-backend-1.onrender.com
   ```

2. **Rebuild and deploy frontend**:
   ```bash
   npm run build
   npm run deploy
   ```

## Database Management

Your PostgreSQL database is already configured:
- **Host**: `dpg-d5mu9275r7bs73dd4fb0-a.oregon-postgres.render.com`
- **Database**: `gymflow_20os`
- **User**: `gymflow_user`
- **Tables**: Automatically created on first run

## Troubleshooting

### Backend Not Starting
- Check Render logs: Dashboard → Your Service → Logs
- Verify all environment variables are set
- Check DATABASE_URL format (should start with `postgresql://`)

### CORS Errors
- Backend already allows `https://kenshar.github.io`
- Check browser console for specific error messages
- Verify frontend is using correct backend URL

### Database Connection Issues
- Verify DATABASE_URL is correct
- Check Render database status
- Ensure database is in same region as web service

## Security Notes

- **SECRET_KEY**: Generate a strong random key for production
- **Database Credentials**: Never commit to version control
- **HTTPS Only**: Render provides free SSL certificates
- **Environment Variables**: Store sensitive data in Render dashboard

## Monitoring

- **Render Dashboard**: Check service health, logs, and metrics
- **Database**: Monitor connections and storage in Render DB dashboard
- **Error Tracking**: Check logs for any API errors or crashes

## Scaling

Free tier limitations:
- Backend sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds
- 750 hours/month free compute time

To prevent sleeping:
- Upgrade to paid plan ($7/month)
- Or set up a cron job to ping the health endpoint every 10 minutes

## Support

- Render Documentation: [render.com/docs](https://render.com/docs)
- Render Community: [community.render.com](https://community.render.com)
- GitHub Issues: Report bugs in the repository
