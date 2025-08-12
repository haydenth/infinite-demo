#!/bin/bash
set -e

echo "Starting database initialization..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL to be ready..."
while ! nc -z infinite-postgres 5432; do
  echo "PostgreSQL is not ready yet. Waiting..."
  sleep 2
done

echo "PostgreSQL is ready. Starting migration process..."

# Initialize Flask-Migrate if needed
if [ ! -d "migrations" ] || [ ! -f "migrations/alembic.ini" ]; then
    echo "Initializing Flask-Migrate..."
    flask db init
fi

# Create migration if no migration files exist
if [ ! "$(ls -A migrations/versions 2>/dev/null)" ]; then
    echo "Creating initial migration..."
    flask db migrate -m "Initial migration with Payment and ExchangeRate models"
fi

# Apply migrations
echo "Applying migrations..."
flask db upgrade

echo "Database initialization complete. Starting Flask application..."

# Start the Flask application
exec flask run --with-threads --host=0.0.0.0 --port=8080 --debugger --reload
