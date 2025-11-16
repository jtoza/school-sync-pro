#!/usr/bin/env bash
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Apply database migrations
python manage.py migrate

# Create or reset admin user
python manage.py create_admin

# Collect static files
python manage.py collectstatic --no-input

# Load your data
python manage.py loaddata data.json || echo "Skipping data load if already exists"