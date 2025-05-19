import os
import shutil
import qrcode
from flask import Flask, request, render_template
from github import Github
from datetime import datetime

app = Flask(__name__)
g = Github(os.getenv("GITHUB_TOKEN"))
repo = g.get_repo("solutionspelichet/businesscard")
branch = repo.get_branch("master")

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        job_title = request.form.get("job_title", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        website = request.form.get("website", "").strip()
        linkedin = request.form.get("linkedin", "").strip()
        company = request.form.get("company", "").strip()

        # ⚠️ Ajoute ici ton traitement si tu veux sauvegarder/générer un fichier ou envoyer une réponse personnalisée

        return f"Formulaire bien reçu pour : {first_name} {last_name} – {job_title} chez {company}"

    return render_template('form.html')

@app.route('/qr/<slug>')
def qr_page(slug):
    return f'''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QR Code - {slug}</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f2f2f2;
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
            }}
            .container {{
                width: 90%;
                max-width: 400px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                text-align: center;
                padding: 20px;
            }}
            .container img {{
                width: 80%;
                max-width: 250px;
                margin-bottom: 20px;
            }}
            .text {{
                font-size: 14px;
                color: #555;
                margin-bottom: 15px;
            }}
            .custom-button {{
                display: block;
                padding: 12px;
                font-size: 15px;
                border-radius: 6px;
                text-align: center;
                margin: 10px auto;
                background-color: #6666ff;
                color: white;
                text-decoration: none;
                width: 80%;
                max-width: 300px;
            }}
            .custom-button:hover {{
                background-color: #4d4ddf;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>Votre QR Code</h2>
            <img src="qrcode.png" alt="QR Code">
            <div class="text">
                Scannez ou enregistrez ce code pour accéder à votre carte de visite.<br>
                Astuce : appuyez longtemps sur le QR code pour l’ajouter à votre écran d’accueil.
            </div>
            <a href="index.html" class="custom-button">⬅ Retour à la carte de visite</a>
        </div>
    </body>
    </html>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    try:
        form_data = {key: request.form.get(key, "").strip() for key in [
            "first_name", "last_name", "job_title", "email",
            "phone", "website", "linkedin", "company"]}

        profile_uploaded = request.files.get("profile")
        office_uploaded = request.files.get("office")

        if not form_data["first_name"] or not form_data["last_name"]:
            return "Erreur : 'first_name' et 'last_name' sont obligatoires."

        first = form_data['first_name'].lower().replace(' ', '_')
        last = form_data['last_name'].lower().replace(' ', '_')
        full_name_slug = f"{first}_{last}"
        full_name = f"{form_data['first_name']} {form_data['last_name']}"

        user_dir = os.path.join("generated", full_name_slug)
        os.makedirs(user_dir, exist_ok=True)

        profile_path = os.path.join(user_dir, "profile.jpg")
        office_path = os.path.join(user_dir, "office.jpg")

        if profile_uploaded and profile_uploaded.filename:
            profile_uploaded.save(profile_path)
        else:
            shutil.copy("static/profile_default.jpg", profile_path)

        if office_uploaded and office_uploaded.filename:
            office_uploaded.save(office_path)
        else:
            shutil.copy("static/office_default.jpg", office_path)

        with open("index_template.html", encoding="utf-8") as f:
            template = f.read()

        rendered = template.format(
            full_name=full_name,
            full_name_slug=full_name_slug,
            job_title=form_data["job_title"],
            email=form_data["email"],
            phone=form_data["phone"],
            website=form_data["website"],
            linkedin=form_data["linkedin"],
            profile_img="profile.jpg",
            office_img="office.jpg",
            company=form_data["company"]
        )

        index_path = os.path.join(user_dir, "index.html")
        with open(index_path, "w", encoding="utf-8") as f:
            f.write(rendered)

        vcard_filename = f"{first}_{last}.vcf"
        vcard_path = os.path.join(user_dir, vcard_filename)
        with open(vcard_path, "w", encoding="utf-8") as v:
            v.write(f"""BEGIN:VCARD
VERSION:3.0
N:{form_data['last_name']};{form_data['first_name']};;;
FN:{full_name}
ORG:{form_data['company']}
TITLE:{form_data['job_title']}
EMAIL:{form_data['email']}
TEL:{form_data['phone']}
URL:{form_data['website']}
END:VCARD
""")

        qr_img_path = os.path.join(user_dir, "qrcode.png")
        qr_url = f"https://solutionspelichet.github.io/businesscard/{full_name_slug}/index.html"
        qr_img = qrcode.make(qr_url)
        qr_img.save(qr_img_path)

        qr_page_path = os.path.join(user_dir, "qr.html")
        with open(qr_page_path, "w", encoding="utf-8") as f:
            f.write(qr_page(full_name_slug))

        def upload_file(filepath, github_path):
            with open(filepath, "rb") as f:
                content = f.read()
            try:
                existing_file = repo.get_contents(github_path, ref=branch.name)
                repo.update_file(github_path, f"Update {github_path}", content, existing_file.sha, branch=branch.name)
            except Exception:
                repo.create_file(github_path, f"Add {github_path}", content, branch=branch.name)

        github_target_path = f"{full_name_slug}/"
        upload_file(profile_path, f"{github_target_path}profile.jpg")
        upload_file(office_path, f"{github_target_path}office.jpg")
        upload_file(index_path, f"{github_target_path}index.html")
        upload_file(vcard_path, f"{github_target_path}{vcard_filename}")
        upload_file(qr_img_path, f"{github_target_path}qrcode.png")
        upload_file(qr_page_path, f"{github_target_path}qr.html")

        card_url = f"https://solutionspelichet.github.io/businesscard/{full_name_slug}/index.html"
        return f"Carte de visite générée : <a href=\"{card_url}\" target=\"_blank\">{card_url}</a>"
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == "__main__":
   import os
port = int(os.environ.get("PORT", 5000))
app.run(debug=True)
