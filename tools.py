import os
import subprocess
from flask import Blueprint, request, send_file, after_this_request
from werkzeug.utils import secure_filename

docx_to_pdf_bp = Blueprint('docx_to_pdf', __name__, template_folder='templates')

UPLOAD_FOLDER = '/home/byteai/mysite/uploads'
CONVERTED_FOLDER = '/home/byteai/mysite/converted'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CONVERTED_FOLDER, exist_ok=True)

# Add 'doc' to allowed extensions
ALLOWED_EXTENSIONS = {'doc', 'docx', 'ppt', 'pptx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@docx_to_pdf_bp.route('/docx_to_pdf', methods=['GET', 'POST'])
def docx_ppt_to_pdf():
    if request.method == 'POST':
        if 'file' not in request.files:
            return 'No file part in request.', 400
        file = request.files['file']
        if file.filename == '':
            return 'No file selected.', 400
        if not allowed_file(file.filename):
            return 'Invalid file type. Only DOC, DOCX, PPT, and PPTX files are allowed.', 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        try:
            subprocess.run(
                ['libreoffice', '--headless', '--convert-to', 'pdf', '--outdir', CONVERTED_FOLDER, filepath],
                check=True
            )
        except subprocess.CalledProcessError:
            return 'Conversion failed.', 500

        pdf_filename = os.path.splitext(filename)[0] + '.pdf'
        pdf_filepath = os.path.join(CONVERTED_FOLDER, pdf_filename)

        if not os.path.exists(pdf_filepath):
            return 'Conversion failed.', 500

        @after_this_request
        def cleanup(response):
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                if os.path.exists(pdf_filepath):
                    os.remove(pdf_filepath)
            except Exception as e:
                print(f"Error cleaning up files: {e}")
            return response

        return send_file(pdf_filepath, as_attachment=True)
