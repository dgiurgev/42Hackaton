from flask import Flask, render_template, request, jsonify
import requests
import os
import json

app = Flask(__name__)

# Lies sensible Daten aus Umgebungsvariablen (im Docker-Container gesetzt)
CLIENT_ID = os.getenv("INTRA42_CLIENT_ID")
CLIENT_SECRET = os.getenv("INTRA42_CLIENT_SECRET")
REDIRECT_URI = "http://91.98.145.248:5000/callback"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
API_ME_URL = "https://api.intra.42.fr/v2/me"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/callback")
def callback():
    print("[1] Callback wurde aufgerufen.")
    

    # 1️⃣ Code aus GET-Parameter holen
    code = request.args.get("code")
    if not code:
        print("Kein Code im Request gefunden.")
        return "Fehler: kein Code erhalten.", 400
    print(f"Code erhalten: {code}")


    # 2️⃣ Access-Token anfordern
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    print("[2] Sende POST-Request an TOKEN_URL...")
    token_resp = requests.post(TOKEN_URL, data=data)
    print(f"Antwort-Status (Token): {token_resp.status_code}")
    print(f"Antwort-Body (Token): {token_resp.text}")

    if token_resp.status_code != 200:
        print("Fehler beim Abrufen des Tokens.")
        return f"Token-Fehler: {token_resp.text}", 400

    tokens = token_resp.json()
    access_token = tokens.get("access_token")
    print(f"Access Token erhalten: {access_token}")


    # 3️⃣ Mit Access-Token Benutzerdaten abfragen
    headers = {"Authorization": f"Bearer {access_token}"}
    print("[3] Sende GET-Request an API_ME_URL...")
    user_resp = requests.get(API_ME_URL, headers=headers)
    print(f"Antwort-Status (User): {user_resp.status_code}")

    if user_resp.status_code != 200:
        print("Fehler bei der Benutzerabfrage.")
        return f"User-Abfrage-Fehler: {user_resp.text}", 400

    user = user_resp.json()
    print("Benutzerinformationen erfolgreich abgerufen:")


    # ==========================
    # Daten extrahieren
    # ==========================
    first_name = user.get("first_name", "")
    last_name = user.get("last_name", "")

    campus_data = user.get("campus", [])
    if campus_data:
        campus_name = campus_data[0].get("name", "")
        campus_address = campus_data[0].get("address", "")
    else:
        campus_name = "Unbekannt"
        campus_address = "-"

    # Projekte filtern: nur finished
    finished_projects = []
    for p in user.get("projects_users", []):
        if p.get("status") == "finished":
            finished_projects.append({
                "name": p.get("project", {}).get("name", "Unbekannt"),
                "final_grade": p.get("final_mark", "n/a"),
            })

    # HTML-Seite rendern
    return render_template(
        "profile.html",
        first_name=first_name,
        last_name=last_name,
        campus_name=campus_name,
        campus_address=campus_address,
        projects=finished_projects
    )

    # # 4️⃣ Ausgabe zur Kontrolle im Browser
    # return jsonify({
    #     "access_token": access_token,
    #     "user": user
    # })


if __name__ == "__main__":
    print("Flask-App gestartet auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
