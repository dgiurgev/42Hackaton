from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    # Gibt die index.html zurück
    return render_template("index.html")

if __name__ == "__main__":
    # host="0.0.0.0" damit der Container von außen erreichbar ist
    app.run(host="0.0.0.0", port=5000, debug=True)
