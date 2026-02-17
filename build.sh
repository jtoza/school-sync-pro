#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Try database migrations but don't fail build if database is unavailable
echo "🔄 Attempting database migrations..."
if python manage.py migrate --no-input; then
    echo "✅ Database migrations successful"
    
    # Create or reset admin user (only if DB is working)
    echo "🔄 Creating admin user..."
    python manage.py create_admin
    
    # Load your data (only if DB is working)
    echo "🔄 Loading initial data..."
    python manage.py loaddata data.json || echo "⚠️ Data load skipped or already exists"
    
    # Create a flag file indicating database is connected
    echo "connected" > db_connected.flag
    echo "✅ Database connection flag set to 'connected'"
else
    echo "⚠️ Database migration failed - database might be unavailable (trial ended?)"
    echo "⚠️ Continuing build without database - will show maintenance page"
    
    # Create a flag file indicating database is disconnected
    echo "disconnected" > db_connected.flag
    echo "📊 Database connection flag set to 'disconnected'"
fi

# Collect static files (this always works, even without DB)
echo "🔄 Collecting static files..."
python manage.py collectstatic --no-input

# Show final status
if [ -f db_connected.flag ]; then
    STATUS=$(cat db_connected.flag)
    if [ "$STATUS" = "connected" ]; then
        echo "✅ Build completed with database connected"
    else
        echo "⚠️ Build completed but database is disconnected - maintenance page active"
    fi
fi