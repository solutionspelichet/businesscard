import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
g = Github(GITHUB_TOKEN)
repo = g.get_repo(GITHUB_REPO)

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
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
        office = request.files['office']

        user_dir = os.path.join("generated", full_name)
        os.makedirs(user_dir, exist_ok=True)

        # Save photo
        photo_path = os.path.join(user_dir, "profil.jpg")
        photo.save(photo_path)

        # Save office photo
        office_path = os.path.join(user_dir, "office.jpg")
        if office and office.filename:
            office.save(office_path)
        else:
            default_office = os.path.join("static", "office.jpg")
            if os.path.exists(default_office):
                with open(default_office, 'rb') as src, open(office_path, 'wb') as dst:
                    dst.write(src.read())

        # Generate VCF
        vcf_content = f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{first_name} {last_name}
TITLE:{job_title}
ORG:{company}
TEL;TYPE=WORK,VOICE:{phone}
EMAIL;TYPE=PREF,INTERNET:{email}
URL:{website}
END:VCARD"""
        vcf_path = os.path.join(user_dir, f"{full_name}.vcf")
        with open(vcf_path, "w") as f:
            f.write(vcf_content.replace("\n", "\r\n"))

        # Generate HTML page
        with open('templates/index_template.html') as tpl_file:
            html_template = tpl_file.read()
        html_filled = html_template.replace("{{FULL_NAME}}", f"{first_name} {last_name}")\
                                     .replace("{{TITLE}}", f"{job_title} - {company}")\
                                     .replace("{{WEBSITE}}", website)\
                                     .replace("{{LINKEDIN}}", linkedin)\
                                     .replace("{{VCF_FILENAME}}", f"{full_name}.vcf")
        html_path = os.path.join(user_dir, "index.html")
        with open(html_path, "w") as f:
            f.write(html_filled)

        # Generate QR code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_name}/index.html"
        qr_path = os.path.join(user_dir, "qr.png")
        qrcode.make(card_url).save(qr_path)

        def upload_file_to_github(local_path, repo_path):
            with open(local_path, 'rb') as file:
                content = file.read()
            try:
                existing = repo.get_contents(repo_path)
                repo.update_file(repo_path, f"update {repo_path}", content, existing.sha)
            except:
                repo.create_file(repo_path, f"add {repo_path}", content)

        # Upload files to GitHub
        upload_file_to_github(html_path, f"{full_name}/index.html")
        upload_file_to_github(photo_path, f"{full_name}/profil.jpg")
        upload_file_to_github(office_path, f"{full_name}/office.jpg")
        upload_file_to_github(qr_path, f"{full_name}/qr.png")
        upload_file_to_github(vcf_path, f"{full_name}/{full_name}.vcf")

        return f"✅ Carte générée pour {first_name} {last_name}. <a href='{card_url}' target='_blank'>Voir la carte</a>"

    except Exception as e:
        return f"❌ Erreur : {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
