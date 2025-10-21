from flask import Flask, render_template, request, jsonify, send_file
import requests
import os
import json
from datetime import datetime
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT

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


def generate_pdf(user_data):
    """Generiert ein PDF aus den Benutzerdaten mit ReportLab"""
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                          leftMargin=2.5*cm, rightMargin=2.5*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    
    # Container für PDF-Elemente
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#404040'),
        spaceAfter=6,
        alignment=TA_RIGHT
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#404040'),
        spaceAfter=3,
        alignment=TA_RIGHT
    )
    
    # Benutzerdaten extrahieren
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
    
    # Header mit Logo und Benutzerinfo
    header_data = []
    
    # Logo hinzufügen (falls vorhanden)
    logo_path = "42HNlogo.png"
    if os.path.exists(logo_path):
        logo = Image(logo_path, width=6*cm, height=2*cm)
        user_info = [
            Paragraph(f"<b>{first_name} {last_name}</b>", title_style),
            Paragraph(f"<b>Core Started:</b> {core_start}", subtitle_style),
            Paragraph(f"<b>Core Completed:</b> {core_end}", subtitle_style),
        ]
        header_data = [[logo, user_info]]
    else:
        # Fallback ohne Logo
        user_info = [
            Paragraph(f"<b>{first_name} {last_name}</b>", title_style),
            Paragraph(f"<b>Core Started:</b> {core_start}", subtitle_style),
            Paragraph(f"<b>Core Completed:</b> {core_end}", subtitle_style),
        ]
        header_data = [["", user_info]]
    
    header_table = Table(header_data, colWidths=[8*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 1*cm))
    
    # Überschrift für Projekte
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=colors.HexColor('#404040'),
        spaceAfter=12,
    )
    elements.append(Paragraph("Project Portfolio", section_title))
    elements.append(Spacer(1, 0.5*cm))
    
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
    
    # Tabelle für Projekte erstellen
    project_data = [["Project", "Description", "Grade"]]
    
    desc_style = ParagraphStyle(
        'DescStyle',
        parent=styles['Normal'],
        fontSize=9,
        leading=11,
    )
    
    for project in finished_projects:
        project_data.append([
            Paragraph(f"<b>{project['name']}</b>", styles['Normal']),
            Paragraph(project['description'], desc_style),
            str(project['final_grade'])
        ])
    
    project_table = Table(project_data, colWidths=[3.5*cm, 10*cm, 2*cm])
    project_table.setStyle(TableStyle([
        # Header
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        
        # Content
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (2, 1), (2, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        
        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
    ]))
    
    elements.append(project_table)
    
    # PDF generieren
    doc.build(elements)
    buffer.seek(0)
    return buffer


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

    try:
        # PDF generieren
        pdf_buffer = generate_pdf(user)
        
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"42_portfolio_{user.get('login', 'user')}.pdf"
        )
    except Exception as e:
        print(f"Fehler beim Generieren des PDFs: {e}")
        import traceback
        traceback.print_exc()
        return f"Fehler beim Generieren des PDFs: {str(e)}", 500


if __name__ == "__main__":
    print("Flask-App gestartet auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)