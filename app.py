import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        
        user_dir = os.path.join("generated", full_name)
        os.makedirs(user_dir, exist_ok=True)

        
        # Champs requis
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if not request.form.get(field):
                return f"Erreur : le champ {field} est requis.", 400

        # Fichier requis
        photo = request.files.get('photo')
        if not photo or photo.filename == "":
            return "Erreur : vous devez téléverser une photo de profil.", 400

        # Lecture des données
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        full_name = f"{first_name}_{last_name}".lower().replace(" ", "_")
        email = request.form.get('email', "")
        phone = request.form.get('phone', "")
        job_title = request.form.get('job_title', "")
        company = request.form.get('company', "")
        linkedin = request.form.get('linkedin', "")
        website = request.form.get('website', "")

        # Création du dossier utilisateur
        user_dir = os.path.join("generated", full_name)
        os.makedirs(user_dir, exist_ok=True)

        # Sauvegarde photo de profil
        photo_path = os.path.join(user_dir, "profil.jpg")
        photo.save(photo_path)

        # Sauvegarde de la photo de bureau (par défaut)
        office_src = os.path.join("static", "office.jpg")
        office_dst = os.path.join(user_dir, "office.jpg")
        if os.path.exists(office_src):
            with open(office_src, 'rb') as src, open(office_dst, 'wb') as dst:
                dst.write(src.read())

        # Création du fichier VCF
        vcf_content = f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{first_name} {last_name}
TITLE:{job_title}
ORG:{company}
TEL;TYPE=WORK,VOICE:{phone}
EMAIL;TYPE=PREF,INTERNET:{email}
URL:{website}
END:VCARD
"""
        vcf_path = os.path.join(user_dir, f"{full_name}.vcf")
        with open(vcf_path, "w", encoding="utf-8") as f:
            f.write(vcf_content.replace("\n", "\r\n"))

        # Lecture du template HTML et génération
        with open('templates/index_template.html', encoding="utf-8") as tpl:
            html_template = tpl.read()
        html_filled = html_template.replace("{{FULL_NAME}}", f"{first_name} {last_name}")\
                                   .replace("{{TITLE}}", f"{job_title} - {company}")\
                                   .replace("{{WEBSITE}}", website)\
                                   .replace("{{LINKEDIN}}", linkedin)\
                                   .replace("{{VCF_FILENAME}}", f"{full_name}.vcf")
        with open(os.path.join(user_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_filled)

        # Génération du QR code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_name}/index.html"
        qr = qrcode.make(card_url)
        qr.save(os.path.join(user_dir, "qr.png"))

        return f"✅ Carte générée pour <strong>{first_name} {last_name}</strong>. <br>Dossier : <code>{user_dir}</code>"

    except Exception as e:
        return f"Erreur : {str(e)}", 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
