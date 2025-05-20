import os
import qrcode
from flask import Flask, render_template, request
from github import Github
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")  # Ex: "solutionspelichet/businesscard"

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    try:
        # 1. Récupération des données
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
        profile_photo = request.files['profile']
        office_photo = request.files['office']

        user_dir = os.path.join("generated", full_slug)
        os.makedirs(user_dir, exist_ok=True)

        # 2. Enregistrement des fichiers
        profile_path = os.path.join(user_dir, "profile.jpg")
        profile_photo.save(profile_path)

        office_path = os.path.join(user_dir, "office.jpg")
        office_photo.save(office_path)

        # 3. VCF
        vcard_filename = f"{full_slug}.vcf"
        vcard_path = os.path.join(user_dir, vcard_filename)
        with open(vcard_path, "w") as vcf:
            vcf.write(f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{full_name}
TITLE:{job_title}
ORG:{company}
TEL:{phone}
EMAIL:{email}
URL:{website}
END:VCARD
""".replace("\n", "\r\n"))

        # 4. QR Code
        card_url = f"https://solutionspelichet.github.io/businesscard/{full_slug}/index.html"
        qr = qrcode.make(card_url)
        qr.save(os.path.join(user_dir, "qr.png"))

        # 5. index.html
        with open("templates/index_template.html", encoding="utf-8") as tpl:
            template = tpl.read()
        rendered = template.format(
            full_name=full_name,
            job_title=job_title,
            company=company,
            website=website,
            linkedin=linkedin,
            vcard_filename=vcard_filename,
            profile_img="profile.jpg",
            office_img="office.jpg"
        )
        with open(os.path.join(user_dir, "index.html"), "w", encoding="utf-8") as html:
            html.write(rendered)

        # 6. qr.html à partir de qr-template
        with open("templates/qr-template.html", encoding="utf-8") as tpl:
            qr_template = tpl.read()
        qr_rendered = qr_template.replace("{full_name}", full_name)
        with open(os.path.join(user_dir, "qr.html"), "w", encoding="utf-8") as f:
            f.write(qr_rendered)

        # 7. Upload GitHub
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        branch = repo.get_branch("master")

        def upload_file(filepath, github_path):
            with open(filepath, "rb") as f:
                content = f.read()
            try:
                existing = repo.get_contents(github_path, ref=branch.name)
                repo.update_file(github_path, f"update {github_path}", content, existing.sha, branch=branch.name)
            except:
                repo.create_file(github_path, f"create {github_path}", content, branch=branch.name)

        github_folder = f"{full_slug}/"
        upload_file(profile_path, github_folder + "profile.jpg")
        upload_file(office_path, github_folder + "office.jpg")
        upload_file(vcard_path, github_folder + vcard_filename)
        upload_file(os.path.join(user_dir, "index.html"), github_folder + "index.html")
        upload_file(os.path.join(user_dir, "qr.png"), github_folder + "qr.png")
        upload_file(os.path.join(user_dir, "qr.html"), github_folder + "qr.html")

        return render_template(
    'confirmation.html',
    full_name=full_name,
    slug=full_slug,
    card_url=card_url
)


    except Exception as e:
        return f"❌ Erreur : {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
