# Basis-Image
FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# LaTeX und notwendige Pakete installieren
RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

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
# Basis-Image
FROM python:3.12-slim

# Arbeitsverzeichnis im Container
WORKDIR /app

# Abhängigkeiten kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App-Code kopieren
COPY app.py .
COPY templates/ ./templates/
COPY static/ ./static/

# Port freigeben
EXPOSE 5000

# Flask starten
# CMD ["tail", "-f"]
CMD ["python", "app.py"]
