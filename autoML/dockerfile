# Utilise une image de base avec Python
FROM python:3.10

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers de l'application dans le conteneur
COPY . /app/

# Installer les dépendances
RUN pip install --upgrade pip && pip install -r requirements.txt

# Exposer le port par défaut de Django (8000)
EXPOSE 8000

# Définir la commande pour démarrer l'application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
