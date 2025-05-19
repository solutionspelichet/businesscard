import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

app = Flask(__name__)

# Load environment variables
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
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
        profile = request.files['photo']
        office = request.files['office']

        user_dir = os.path.join("generated", full_slug)
        os.makedirs(user_dir, exist_ok=True)

        profile_path = os.path.join(user_dir, "profile.jpg")
        profile.save(profile_path)

        office_path = os.path.join(user_dir, "office.jpg")
        office.save(office_path)

        # VCF
        vcard_filename = f"{full_slug}.vcf"
        vcard_path = os.path.join(user_dir, vcard_filename)
        vcf_content = f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{full_name}
TITLE:{job_title}
ORG:{company}
TEL;TYPE=WORK,VOICE:{phone}
EMAIL;TYPE=PREF,INTERNET:{email}
URL:{website}
END:VCARD
"""
        with open(vcard_path, "w") as f:
            f.write(vcf_content.replace("\n", "\r\n"))

        # HTML
        with open('templates/index_template.html') as tpl_file:
            template = tpl_file.read()
        html_filled = template.format(
            full_name=full_name,
            job_title=job_title,
            company=company,
            website=website,
            linkedin=linkedin,
            vcard_filename=vcard_filename,
            profile_img="profile.jpg",
            office_img="office.jpg"
        )
        with open(os.path.join(user_dir, "index.html"), "w") as f:
            f.write(html_filled)

        # QR Code
        url = f"https://solutionspelichet.github.io/businesscard/{full_slug}/index.html"
        qr = qrcode.make(url)
        qr.save(os.path.join(user_dir, "qr.png"))

        return f"Carte de visite générée : <a href='{url}'>{url}</a>"

    except Exception as e:
        return f"Erreur : {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
