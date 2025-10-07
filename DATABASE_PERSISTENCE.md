# Railway Database Persistence Setup

## The Problem
Railway PostgreSQL containers are **ephemeral** and get recreated on each deployment, causing data loss.

## Solutions Implemented

### 1. **Flask-Migrate Integration**
- Added proper database migration system
- Prevents schema conflicts during deployments
- Handles database structure changes gracefully

### 2. **Database Backup/Restore System**
- Automatic backup functionality via `/admin/backup` endpoint
- Restore functionality via `/admin/restore` endpoint
- Command-line backup tool (`manage_db.py`)

### 3. **Railway Configuration**
- Added `railway.json` for proper deployment configuration
- Configured health checks and restart policies

## How to Preserve Data Across Deployments

### **Option A: Use Railway's Persistent PostgreSQL (Recommended)**

1. **In Railway Dashboard:**
   - Go to your project
   - Add a **PostgreSQL** service (not the ephemeral one)
   - Connect it to your web service
   - Railway will provide a persistent `DATABASE_URL`

2. **The database will persist across deployments!**

### **Option B: Manual Backup Before Deployments**

1. **Before each deployment:**
   ```bash
   # Create backup
   curl https://your-app.railway.app/admin/backup > backup.json
   
   # Or use the management script locally
   python manage_db.py backup
   ```

2. **After deployment:**
   ```bash
   # Restore from backup
   curl -X POST https://your-app.railway.app/admin/restore \
        -H "Content-Type: application/json" \
        -d @backup.json
   ```

### **Option C: Automated Backup System**

Add this to your Railway deployment:

1. **Create a backup service** that runs periodically
2. **Store backups** in Railway's persistent volume or external storage
3. **Auto-restore** on deployment

## Commands

### **Local Database Management:**
```bash
# Show database stats
python manage_db.py stats

# Create backup
python manage_db.py backup my_backup.json

# Restore from backup
python manage_db.py restore my_backup.json
```

### **API Endpoints:**
- `GET /admin/backup` - Download backup as JSON
- `POST /admin/restore` - Restore from JSON backup
- `GET /admin/stats` - View database statistics

## Migration Commands (if needed):
```bash
# Initialize migrations (first time only)
flask db init

# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade
```

## Important Notes:

1. **Railway PostgreSQL is persistent** - the issue might be configuration
2. **Check your Railway dashboard** - ensure you're using a persistent PostgreSQL service
3. **Environment variables** - Railway should automatically provide `DATABASE_URL`
4. **Backup regularly** - especially before major deployments

## Troubleshooting:

- **Data still disappearing?** Check if you're using the ephemeral PostgreSQL vs persistent PostgreSQL
- **Connection errors?** Verify `DATABASE_URL` is set correctly in Railway
- **Migration issues?** Use `flask db upgrade` to apply pending migrations
