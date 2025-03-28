from flask import Flask, request, jsonify, render_template
import os
import shutil
from werkzeug.utils import secure_filename
import subprocess

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Anki media directory - using local directory
ANKI_MEDIA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')

# Ensure Anki media directory exists
os.makedirs(ANKI_MEDIA_DIR, exist_ok=True)

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle .apkg file uploads"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if not file.filename.endswith('.apkg'):
        return jsonify({'error': 'File must be an .apkg file'}), 400
    
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(ANKI_MEDIA_DIR, filename)
        file.save(filepath)
        
        # Change ownership to abc:abc
        subprocess.run(['chown', 'abc:abc', filepath])
        
        app.logger.info(f"Successfully saved {filename} to {filepath}")
        return jsonify({'message': 'File uploaded successfully'})
    except Exception as e:
        app.logger.error(f"Error saving file: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 