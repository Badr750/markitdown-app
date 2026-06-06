import os
import uuid
from flask import Flask, request, jsonify, send_file, render_template
from markitdown import MarkItDown
from werkzeug.utils import secure_filename

os.makedirs('uploads', exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit

ALLOWED_EXTENSIONS = {
    'pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'ppt',
    'csv', 'json', 'xml', 'html', 'htm', 'txt', 'md',
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'zip'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': f'File type not supported'}), 400

    # Save uploaded file temporarily
    filename = secure_filename(file.filename)
    unique_name = f"{uuid.uuid4()}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
    file.save(filepath)

    try:
        md = MarkItDown()
        result = md.convert(filepath)
        markdown_text = result.text_content

        # Save markdown output
        md_filename = os.path.splitext(filename)[0] + '.md'
        md_filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{md_filename}")
        with open(md_filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_text)

        return jsonify({
            'markdown': markdown_text,
            'download_token': os.path.basename(md_filepath),
            'original_name': md_filename
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        # Clean up uploaded file
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/download/<token>')
def download(token):
    # Basic security: only allow files in upload folder, no path traversal
    safe_token = secure_filename(token)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_token)
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404
    return send_file(filepath, as_attachment=True, download_name=safe_token.split('_', 1)[-1])

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
