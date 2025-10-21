# Basis-Image
FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code und Assets kopieren
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/
COPY 42HNlogo.png .

# Port freigeben
EXPOSE 5000

# Flask starten
CMD ["python", "app.py"]
