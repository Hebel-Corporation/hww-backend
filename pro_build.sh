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
    if [[ -z "$HWW_SUPERUSER_USERNAME" || -z "$HWW_SUPERUSER_PASSWORD" ]]; then
        echo "Erreur : Les variables HWW_SUPERUSER_USERNAME et HWW_SUPERUSER_PASSWORD doivent être définies."
        exit 1
    fi

    # Créer le superutilisateur via un script Python pour inclure le mot de passe
    python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='$HWW_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser('$HWW_SUPERUSER_USERNAME', '$HWW_SUPERUSER_PASSWORD')
    print("Superutilisateur créé avec succès")
else:
    print("Le superutilisateur existe déjà")
END
fi
