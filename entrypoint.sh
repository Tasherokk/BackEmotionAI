#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
while ! nc -z db 5432; do
  sleep 0.1
done
echo "PostgreSQL is ready!"

echo "Running database migrations..."
python server/manage.py migrate --noinput

echo "Collecting static files..."
python server/manage.py collectstatic --noinput

echo "Starting Django server..."
exec "$@"
