from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)

# Lies sensible Daten aus Umgebungsvariablen (besser als direkt im Code)
# CLIENT_ID = os.getenv("INTRA42_CLIENT_ID", "u-xxxxxx")
# CLIENT_SECRET = os.getenv("INTRA42_CLIENT_SECRET", "s-xxxxxx")
CLIENT_ID = os.getenv("INTRA42_CLIENT_ID")
CLIENT_SECRET = os.getenv("INTRA42_CLIENT_SECRET")
REDIRECT_URI = "http://91.98.145.248/callback"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
API_ME_URL = "https://api.intra.42.fr/v2/me"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/callback")
def callback():
    # 1️⃣ Code aus GET-Parameter holen
    code = request.args.get("code")
    if not code:
        return "Fehler: kein Code erhalten.", 400

    # 2️⃣ Access-Token anfordern
    data = {
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    token_resp = requests.post(TOKEN_URL, data=data)
    if token_resp.status_code != 200:
        return f"Token-Fehler: {token_resp.text}", 400

    tokens = token_resp.json()
    access_token = tokens.get("access_token")

    # 3️⃣ Mit Access-Token Benutzerdaten abfragen (Test)
    headers = {"Authorization": f"Bearer {access_token}"}
    user_resp = requests.get(API_ME_URL, headers=headers)
    if user_resp.status_code != 200:
        return f"User-Abfrage-Fehler: {user_resp.text}", 400

    user = user_resp.json()

    # 4️⃣ Ausgabe zur Kontrolle
    return jsonify({
        "access_token": access_token,
        "user": {
            "login": user.get("login"),
            "email": user.get("email"),
            "image": user.get("image", {}).get("link"),
        }
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
