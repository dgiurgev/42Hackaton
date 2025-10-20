# Basis-Image
FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY app.py .

# Port freigeben
EXPOSE 5000

# Flask starten
CMD ["python", "app.py"]
