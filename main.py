import os
import fitz
from flask import Flask, request, render_template, redirect, url_for, send_file, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('static', exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def convert_pdf_to_html(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        html_content = []
        
        html_content.append("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Converted PDF</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .page { margin-bottom: 50px; padding: 20px; border: 1px solid #ddd; }
        .page-number { font-weight: bold; color: #666; margin-bottom: 20px; }
    </style>
</head>
<body>
""")
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            page_html = page.get_text("html")
            
            html_content.append(f'<div class="page">')
            html_content.append(f'<div class="page-number">Page {page_num + 1}</div>')
            html_content.append(page_html)
            html_content.append('</div>')
        
        html_content.append("""
</body>
</html>
""")
        
        doc.close()
        return ''.join(html_content)
    
    except Exception as e:
        raise Exception(f"Error converting PDF: {str(e)}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    
    if file.filename == '':
        flash('No file selected')
        return redirect(request.url)
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            html_content = convert_pdf_to_html(filepath)
            
            result_path = os.path.join('static', 'result.html')
            with open(result_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            os.remove(filepath)
            
            return redirect(url_for('result'))
        
        except Exception as e:
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Error processing file: {str(e)}')
            return redirect(url_for('index'))
    
    else:
        flash('Invalid file type. Please upload a PDF file.')
        return redirect(url_for('index'))

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/view')
def view_html():
    return send_file('static/result.html')

@app.route('/download')
def download_html():
    return send_file('static/result.html', as_attachment=True, download_name='converted.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
