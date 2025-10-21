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
from flask import Flask, render_template, request, jsonify, send_file
import requests
import os
import json
import subprocess
from datetime import datetime

app = Flask(__name__)

# Lies sensible Daten aus Umgebungsvariablen (im Docker-Container gesetzt)
CLIENT_ID = os.getenv("INTRA42_CLIENT_ID")
CLIENT_SECRET = os.getenv("INTRA42_CLIENT_SECRET")
REDIRECT_URI = "http://91.98.145.248:5000/callback"
TOKEN_URL = "https://api.intra.42.fr/oauth/token"
API_ME_URL = "https://api.intra.42.fr/v2/me"

# Projekt-Beschreibungen (manuell gepflegt)
PROJECT_DESCRIPTIONS = {
    "libft": "A custom C library implementing standard functions from scratch, including string manipulation, memory operations, and linked list utilities.",
    "ft_printf": "Recreation of the printf function in C, handling various format specifiers and conversion flags.",
    "get_next_line": "A function that reads a line from a file descriptor, demonstrating file I/O and memory management.",
    "Born2beroot": "System administration project involving virtual machine setup, user management, and security configuration.",
    "so_long": "A 2D game project using the MiniLibX graphics library, implementing game mechanics and sprite rendering.",
    "push_swap": "Algorithm project to sort data on a stack with a limited set of operations, optimizing for minimal moves.",
    "minitalk": "Inter-process communication project using UNIX signals to transmit data between client and server.",
    "Philosophers": "Threading and synchronization project simulating the dining philosophers problem.",
    "minishell": "A simple shell implementation in C, handling command parsing, execution, and built-in commands.",
    "NetPractice": "Network configuration exercises to understand TCP/IP addressing and routing.",
    "cub3d": "A 3D game engine using raycasting technique, inspired by Wolfenstein 3D.",
    "CPP Module 00": "Introduction to C++, covering basic syntax, classes, and member functions.",
    "CPP Module 01": "Memory allocation, references, pointers to members, and switch statements in C++.",
    "CPP Module 02": "Ad-hoc polymorphism, operator overloading, and orthodox canonical class form.",
    "CPP Module 03": "Inheritance in C++, demonstrating class hierarchies and virtual functions.",
    "CPP Module 04": "Subtype polymorphism, abstract classes, and interfaces in C++.",
    "CPP Module 05": "Exception handling and repetition in C++.",
    "CPP Module 06": "C++ type casting and conversion operators.",
    "CPP Module 07": "C++ templates and generic programming.",
    "CPP Module 08": "Templated containers, iterators, and algorithms in C++.",
    "CPP Module 09": "STL containers and advanced C++ concepts.",
    "ft_irc": "IRC server implementation in C++, handling multiple clients and channels.",
    "Inception": "Docker infrastructure project, setting up multiple services with docker-compose.",
    "ft_transcendence": "Full-stack web application project with real-time features and game implementation.",
}


def get_project_description(project_name):
    """Gibt die Beschreibung für ein Projekt zurück oder Platzhalter-Text"""
    return PROJECT_DESCRIPTIONS.get(
        project_name,
        "This project demonstrates advanced programming concepts and problem-solving skills."
    )


def format_date(date_string):
    """Konvertiert ISO-Datum in lesbares Format"""
    if not date_string:
        return "N/A"
    try:
        dt = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y")
    except:
        return date_string


def escape_latex(text):
    """Escaped Sonderzeichen für LaTeX"""
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\^{}',
        '\\': r'\textbackslash{}',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def generate_latex_pdf(user_data, output_path="output"):
    """Generiert ein PDF aus den Benutzerdaten"""
    
    first_name = user_data.get("first_name", "")
    last_name = user_data.get("last_name", "")
    
    # Core Curriculum Daten finden
    cursus_users = user_data.get("cursus_users", [])
    core_start = "N/A"
    core_end = "N/A"
    
    for cursus in cursus_users:
        if cursus.get("cursus_id") == 21:
            core_start = format_date(cursus.get("begin_at"))
            if cursus.get("end_at"):
                core_end = format_date(cursus.get("end_at"))
            else:
                core_end = "In Progress"
            break
    
    # Projekte filtern: nur finished mit cursus_id 21
    finished_projects = []
    for p in user_data.get("projects_users", []):
        if p.get("status") == "finished" and p.get("cursus_ids", []):
            if 21 in p.get("cursus_ids", []):
                project_name = p.get("project", {}).get("name", "Unknown")
                finished_projects.append({
                    "name": project_name,
                    "description": get_project_description(project_name),
                    "final_grade": p.get("final_mark", "N/A"),
                })
    
    # LaTeX-Template erstellen
    latex_content = r"""\documentclass[a4paper,11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{tabularx}
\usepackage{booktabs}
\usepackage{xcolor}
\usepackage{fancyhdr}
\usepackage{array}

\geometry{left=2.5cm, right=2.5cm, top=3cm, bottom=2.5cm}

\pagestyle{fancy}
\fancyhf{}
\renewcommand{\headrulewidth}{0pt}
\fancyfoot[C]{\thepage}

\definecolor{darkgray}{RGB}{64,64,64}
\definecolor{lightgray}{RGB}{240,240,240}

\begin{document}

% Header
\noindent
\begin{minipage}[t]{0.5\textwidth}
    \includegraphics[width=0.6\textwidth]{42HNlogo.png}
\end{minipage}%
\begin{minipage}[t]{0.5\textwidth}
    \raggedleft
    \textbf{\Large """ + escape_latex(first_name) + r""" """ + escape_latex(last_name) + r"""}\\[0.5em]
    \textcolor{darkgray}{
        \textbf{Core Started:} """ + escape_latex(core_start) + r"""\\
        \textbf{Core Completed:} """ + escape_latex(core_end) + r"""
    }
\end{minipage}

\vspace{2em}

\section*{Project Portfolio}

\begin{tabularx}{\textwidth}{>{\bfseries}p{3.5cm}X>{\centering\arraybackslash}p{1.8cm}}
\toprule
\textbf{Project} & \textbf{Description} & \textbf{Grade} \\
\midrule
"""

    # Projekte hinzufügen
    for i, project in enumerate(finished_projects):
        if i > 0:
            latex_content += r"\midrule" + "\n"
        
        latex_content += escape_latex(project["name"]) + " & "
        latex_content += escape_latex(project["description"]) + " & "
        latex_content += str(project["final_grade"]) + r" \\" + "\n"
    
    latex_content += r"""\bottomrule
\end{tabularx}

\end{document}"""
    
    # LaTeX-Datei schreiben
    tex_file = f"{output_path}.tex"
    with open(tex_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    # PDF kompilieren
    try:
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file],
            check=True,
            capture_output=True,
            cwd=os.path.dirname(os.path.abspath(tex_file)) or '.'
        )
        # Zweimal kompilieren für korrekte Referenzen
        subprocess.run(
            ['pdflatex', '-interaction=nonstopmode', tex_file],
            check=True,
            capture_output=True,
            cwd=os.path.dirname(os.path.abspath(tex_file)) or '.'
        )
        return f"{output_path}.pdf"
    except subprocess.CalledProcessError as e:
        print(f"Fehler beim Kompilieren: {e}")
        return None


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
    print("Benutzerinformationen erfolgreich abgerufen.")

    # PDF generieren
    pdf_path = generate_latex_pdf(user, output_path="/tmp/portfolio")
    
    if pdf_path and os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True, download_name="42_portfolio.pdf")
    else:
        return "Fehler beim Generieren des PDFs.", 500


if __name__ == "__main__":
    print("Flask-App gestartet auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)