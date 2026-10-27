#!/bin/sh
set -e

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Create superuser if not exists
echo "Checking for admin user..."
python scripts/create_admin.py || true

# Execute the command
exec "$@"
