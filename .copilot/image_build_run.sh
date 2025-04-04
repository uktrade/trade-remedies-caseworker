#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

export API_BASE_URL=http://api:8000
export DJANGO_SECRET_KEY="example"
export DATABASE_URL=psql://postgres:postgres@localhost:5432/trade_remedies
export DJANGO_SETTINGS_MODULE="config.settings.staging"

cd trade_remedies_caseworker
python manage.py collectstatic --noinput
