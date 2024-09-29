#!/usr/bin/env bash
# exit on error

set -o errexit

pip install -r requirements.txt

python manage.py makemigrations
python manage.py collectstatic --no-input
python manage.py migrate

# Charger les fixtures
python manage.py loaddata fixtures/*.json

if [[ "${CREATE_SUPERUSER,,}" == "true" ]]; then
    python manage.py createsuperuser --no-input --username "$HWW_SUPERUSER_USERNAME" --email "$HWW_SUPERUSER_EMAIL" --password "$HWW_SUPERUSER_PASSWORD"
fi