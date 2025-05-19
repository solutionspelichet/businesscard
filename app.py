import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

# Initialisation de l'app Flask
app = Flask(__name__)

# Chargement des variables d'environnement
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# 📁 Dossiers principaux
STATIC_DIR = os.path.join("static")
UPLOAD_DIR = os.path.join(STATIC_DIR, "uploads")
GENERATED_DIR = os.path.join("generated")

# 📁 Création des dossiers nécessaires au démarrage
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(GENERATED_DIR, exist_ok=True)
print(f"✅ Dossier UPLOAD créé : {UPLOAD_DIR}")
print(f"✅ Dossier GENERATED créé : {GENERATED_DIR}")

# 🔁 Route d’accueil
@app.route('/')
def form():
    return render_template('form.html')

# 🚀 Soumission du formulaire
@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 🔤 Lecture des champs
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        full_name = f"{first_name}_{last_name}".lower().replace(" ", "_")

        # 📁 Création du dossier utilisateur
        user_dir = os.path.join(GENERATED_DIR, full_name)
        os.makedirs(user_dir, exist_ok=True)
        print(f"✅ Dossier utilisateur créé : {user_dir}")

        # 📧 Autres infos
        email = request.form['email']
        phone = request.form['phone']
        job_title = request.form['job_title']
        company = request.form['company']
        linkedin = request.form['linkedin']
        website = request.form['website']
        photo = request.files['photo']

        # 📸 Sauvegarde de la photo
        photo_path = os.path.join(user_dir, "profil.jpg")
        photo.save(photo_path)

        # 🏢 Copie de l’image du bureau
        office_src = os.path.join(STATIC_DIR, "office.jpg")
        office_dst = os.path.join(user_dir, "office.jpg")
        if os.path.exists(office_src):
            with open(office_src, 'rb') as src, open(office_dst, 'wb') as dst:
                dst.write(src.read())

        # 📇 Génération du fichier VCF
        vcf_content = "BEGIN:VCARD\nVERSION:3.0\n"
        vcf_content += f"N:{last_name};{first_name}\n"
        vcf_content += f"FN:{first_name} {last_name}\n"
        vcf_content += f"TITLE:{job_title}\n"
        vcf_content += f"ORG:{company}\n"
        vcf_content += f"TEL;TYPE=WORK,VOICE:{phone}\n"
        vcf_content += f"EMAIL;TYPE=PREF,INTERNET:{email}\n"
        vcf_content += f"URL:{website}\nEND:VCARD"
        with open(os.path.join(user_dir, f"{full_name}.vcf"), "w") as f:
            f.write(vcf_content.replace("\n", "\r\n"))

        # 🧾 Génération de la page HTML
        with open('templates/index_template.html') as tpl_file:
            html_template = tpl_file.read()
        html_filled = html_template.replace("{{FULL_NAME}}", f"{first_name} {last_name}")\
                                   .replace("{{TITLE}}", f"{job_title} - {company}")\
                                   .replace("{{WEBSITE}}", website)\
                                   .replace("{{LINKEDIN}}", linkedin)\
                                   .replace("{{VCF_FILENAME}}", f"{full_name}.vcf")
        with open(os.path.join(user_dir, "index.html"), "w") as f:
            f.write(html_filled)

        # 📲 Génération du QR code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_name}/index.html"
        qr = qrcode.make(card_url)
        qr.save(os.path.join(user_dir, "qr.png"))

        return f"✅ Carte générée pour {first_name} {last_name}.<br>Dossier : {user_dir}"

    except Exception as e:
        return f"❌ Erreur : {e}"

# ▶️ Lancement en local ou sur Render
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
