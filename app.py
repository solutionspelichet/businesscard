import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

# Initialisation Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Chargement des variables d’environnement
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

# Connexion à GitHub
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)
branch = repo.get_branch("master")

# Fonction d'upload d'un fichier vers GitHub
def upload_file(filepath, github_path):
    with open(filepath, "rb") as f:
        content = f.read()
    try:
        existing = repo.get_contents(github_path, ref=branch.name)
        repo.update_file(github_path, f"Update {github_path}", content, existing.sha, branch=branch.name)
    except Exception:
        repo.create_file(github_path, f"Add {github_path}", content, branch=branch.name)

# Page formulaire
@app.route('/')
def form():
    return render_template('form.html')

# Traitement du formulaire
@app.route('/submit', methods=['POST'])
def submit():
    try:
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        full_name = f"{first_name}_{last_name}".lower().replace(" ", "_")
        full_name_display = f"{first_name} {last_name}"

        email = request.form['email']
        phone = request.form['phone']
        job_title = request.form['job_title']
        company = request.form['company']
        linkedin = request.form['linkedin']
        website = request.form['website']
        photo = request.files['photo']
        office = request.files['office']

        # Création du répertoire local
        user_dir = os.path.join("generated", full_name)
        os.makedirs(user_dir, exist_ok=True)

        # Sauvegarde images
        photo_path = os.path.join(user_dir, "profile.jpg")
        office_path = os.path.join(user_dir, "office.jpg")
        photo.save(photo_path)
        office.save(office_path)

        # vCard
        vcard_path = os.path.join(user_dir, f"{full_name}.vcf")
        with open(vcard_path, "w", encoding="utf-8") as f:
            f.write(f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{first_name} {last_name}
TITLE:{job_title}
ORG:{company}
TEL;TYPE=WORK,VOICE:{phone}
EMAIL;TYPE=PREF,INTERNET:{email}
URL:{website}
END:VCARD""".replace("\n", "\r\n"))

        # Page HTML
        with open('templates/index_template.html', encoding="utf-8") as f:
            template = f.read()
        html_filled = template.format(
    full_name=full_name_display,
    job_title=job_title,
    company=company,
    website=website,
    linkedin=linkedin,
    vcard_filename=f"{full_name}.vcf"
        )
        index_path = os.path.join(user_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(html_filled)

        # QR Code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_name}/index.html"
        qr_img = qrcode.make(card_url)
        qr_path = os.path.join(user_dir, "qr.png")
        qr_img.save(qr_path)

        # QR page HTML
        qr_html = f"""<html><body><h1>QR Code</h1><img src='qr.png'><br><a href='index.html'>Retour</a></body></html>"""
        qr_html_path = os.path.join(user_dir, "qr.html")
        with open(qr_html_path, "w", encoding="utf-8") as f:
            f.write(qr_html)

        # Upload vers GitHub
        github_path = f"{full_name}/"
        upload_file(photo_path, github_path + "profile.jpg")
        upload_file(office_path, github_path + "office.jpg")
        upload_file(index_path, github_path + "index.html")
        upload_file(vcard_path, github_path + f"{full_name}.vcf")
        upload_file(qr_path, github_path + "qr.png")
        upload_file(qr_html_path, github_path + "qr.html")

        return f"✅ Carte générée avec succès : <a href='{card_url}' target='_blank'>{card_url}</a>"

    except Exception as e:
        return f"❌ Erreur : {e}"

# Lancement local
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
