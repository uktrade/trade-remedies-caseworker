#!/usr/bin/env bash

# Exit early if something goes wrong
set -e

cd trade_remedies_caseworker
python manage.py collectstatic --noinput