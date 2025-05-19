import os
import qrcode
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename

app = Flask(__name__)

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

        user_dir = os.path.join("generated", full_slug)
        os.makedirs(user_dir, exist_ok=True)

        job_title = request.form['job_title']
        company = request.form['company']
        email = request.form['email']
        phone = request.form['phone']
        website = request.form['website']
        linkedin = request.form['linkedin']

        profile_img = request.files.get('photo')
        office_img = request.files.get('office')

        profile_path = os.path.join(user_dir, "profile.jpg")
        office_path = os.path.join(user_dir, "office.jpg")

        if profile_img:
            profile_img.save(profile_path)
        if office_img:
            office_img.save(office_path)

        vcard_path = os.path.join(user_dir, f"{full_slug}.vcf")
        with open(vcard_path, "w") as vcf:
            vcf.write(f"""BEGIN:VCARD
VERSION:3.0
N:{last_name};{first_name}
FN:{full_name}
ORG:{company}
TITLE:{job_title}
EMAIL:{email}
TEL:{phone}
URL:{website}
END:VCARD
""")

        with open("templates/index_template.html", "r", encoding="utf-8") as tpl:
            html_template = tpl.read()

        html_filled = html_template\
            .replace("{ full_name }", full_name)\
            .replace("{ job_title }", job_title)\
            .replace("{ company }", company)\
            .replace("{ website }", website)\
            .replace("{ linkedin }", linkedin)\
            .replace("{ vcard_filename }", f"{full_slug}.vcf")

        with open(os.path.join(user_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_filled)

        qr_path = os.path.join(user_dir, "qr.png")
        qr_url = f"https://solutionspelichet.github.io/businesscard/{full_slug}/index.html"
        qrcode.make(qr_url).save(qr_path)

        return f"Carte de visite générée avec succès : {qr_url}"
    except Exception as e:
        return f"Erreur : {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
