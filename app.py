import os
import qrcode
from flask import Flask, render_template, request
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Récupération des données du formulaire
        first_name = request.form['first_name'].strip()
        last_name = request.form['last_name'].strip()
        full_name = f"{first_name} {last_name}"
        full_slug = f"{first_name}_{last_name}".lower().replace(" ", "_")
        email = request.form['email']
        phone = request.form['phone']
        job_title = request.form['job_title']
        company = request.form['company']
        linkedin = request.form['linkedin']
        website = request.form['website']

        profile = request.files['profile']
        office = request.files['office']

        # Création du répertoire utilisateur
        user_dir = os.path.join("generated", full_slug)
        os.makedirs(user_dir, exist_ok=True)

        # Enregistrement des images
        profile_path = os.path.join(user_dir, "profile.jpg")
        profile.save(profile_path)
        office_path = os.path.join(user_dir, "office.jpg")
        office.save(office_path)

        # Création du fichier VCF
        vcard_filename = f"{full_slug}.vcf"
        vcard_path = os.path.join(user_dir, vcard_filename)
        with open(vcard_path, "w", encoding="utf-8") as f:
            f.write(f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{full_name}
ORG:{company}
TITLE:{job_title}
EMAIL:{email}
TEL:{phone}
URL:{website}
END:VCARD""")

        # Génération du QR code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_slug}/index.html"
        qr_path = os.path.join(user_dir, "qr.png")
        qr = qrcode.make(card_url)
        qr.save(qr_path)

        # Création du fichier HTML à partir du template
        with open("templates/index_template.html", encoding="utf-8") as tpl_file:
            html_template = tpl_file.read()

        html_filled = html_template.format(
            full_name=full_name,
            job_title=job_title,
            company=company,
            website=website,
            linkedin=linkedin,
            vcard_filename=vcard_filename,
            profile_img="profile.jpg",
            office_img="office.jpg"
        )

        with open(os.path.join(user_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_filled)

        return f"Carte générée pour {full_name}. Dossier : {user_dir}"
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
