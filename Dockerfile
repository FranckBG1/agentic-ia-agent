FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier requirements.txt en premier (pour cache Docker)
COPY requirements.txt .

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le code source
COPY . .

# Variables d'environnement
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/serviceAccountKey.json

# Exposer le port
EXPOSE 8080

# Commande de démarrage
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app