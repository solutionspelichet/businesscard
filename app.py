from flask import Flask, render_template, request, redirect
import os
import qrcode
from github import Github
from dotenv import load_dotenv
from datetime import datetime

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
    first_name = request.form['first_name'].strip()
    last_name = request.form['last_name'].strip()
    full_name = f"{first_name}_{last_name}".lower().replace(" ", "_")
    email = request.form['email']
    phone = request.form['phone']
    job_title = request.form['job_title']
    company = request.form['company']
    linkedin = request.form['linkedin']
    website = request.form['website']
    photo = request.files['photo']
    
    user_dir = os.path.join("generated", full_name)
    os.makedirs(user_dir, exist_ok=True)

    # Sauvegarde de la photo
    photo_path = os.path.join(user_dir, "profil.jpg")
    photo.save(photo_path)

    # Copier l’image commune
    office_src = os.path.join("static", "office.jpg")
    office_dst = os.path.join(user_dir, "office.jpg")
    if os.path.exists(office_src):
        with open(office_src, 'rb') as src, open(office_dst, 'wb') as dst:
            dst.write(src.read())

    # Génération fichier VCF
    vcf_content = "BEGIN:VCARD\nVERSION:3.0\n"
    vcf_content += f"N:{last_name};{first_name}\n"
    vcf_content += f"FN:{first_name} {last_name}\n"
    vcf_content += f"TITLE:{job_title}\n"
    vcf_content += f"ORG:{company}\n"
    vcf_content += f"TEL;TYPE=WORK,VOICE:{phone}\n"
    vcf_content += f"EMAIL;TYPE=PREF,INTERNET:{email}\n"
    vcf_content += f"URL:{website}\nEND:VCARD"
    with open(os.path.join(user_dir, f"{first_name}_{last_name}.vcf"), "w") as f:
        f.write(vcf_content.replace("\n", "\r\n"))

    # Génération page HTML
    with open('templates/index_template.html') as tpl_file:
        html_template = tpl_file.read()
    html_filled = html_template.replace("{{FULL_NAME}}", f"{first_name} {last_name}")\
                                .replace("{{TITLE}}", f"{job_title} - {company}")\
                                .replace("{{WEBSITE}}", website)\
                                .replace("{{LINKEDIN}}", linkedin)\
                                .replace("{{VCF_FILENAME}}", f"{first_name}_{last_name}.vcf")
    with open(os.path.join(user_dir, "index.html"), "w") as f:
        f.write(html_filled)

    # Génération QR code
    card_url = f"https://solutionspelichet.github.io/businesscard/{full_name}/index.html"
    qr = qrcode.make(card_url)
    qr.save(os.path.join(user_dir, "qr.png"))

    return f"Carte générée pour {first_name} {last_name}. Dossier : {user_dir}"

if __name__ == '__main__':
    app.run(debug=True)
