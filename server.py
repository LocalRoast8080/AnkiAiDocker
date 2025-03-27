from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import os
import shutil
from urllib.parse import parse_qs

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory to store uploaded .apkg files
UPLOAD_DIR = "/config/app/Anki2/User 1/collection.media"

class AnkiRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            # Check if this is a multipart form data upload
            if 'content-type' in self.headers:
                content_type = self.headers['content-type']
                if 'boundary=' in content_type:
                    # Handle file upload
                    self.handle_file_upload()
                    return

            # Handle regular JSON requests
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length).decode('utf-8')
            logger.info(f"Received request: {body}")

            request = json.loads(body)
            response = {
                "status": "success",
                "message": "Request received",
                "data": request
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

    def handle_file_upload(self):
        try:
            # Read the multipart form data
            content_type = self.headers['content-type']
            boundary = content_type.split('boundary=')[1]
            
            # Read the request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            # Parse the multipart data
            parts = body.split(boundary.encode())
            
            for part in parts:
                if b'filename=' in part:
                    # Extract filename
                    filename = part.split(b'filename="')[1].split(b'"')[0].decode()
                    
                    # Only process .apkg files
                    if filename.endswith('.apkg'):
                        # Extract file content
                        file_content = part.split(b'\r\n\r\n')[1]
                        
                        # Save the file
                        file_path = os.path.join(UPLOAD_DIR, filename)
                        with open(file_path, 'wb') as f:
                            f.write(file_content)
                        
                        logger.info(f"Successfully uploaded {filename}")
                        
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            "status": "success",
                            "message": f"File {filename} uploaded successfully"
                        }).encode('utf-8'))
                        return
            
            # If no .apkg file was found
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": "No .apkg file found in upload"
            }).encode('utf-8'))

        except Exception as e:
            logger.error(f"Error handling file upload: {str(e)}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "error",
                "message": str(e)
            }).encode('utf-8'))

    def do_OPTIONS(self):
        # Handle CORS preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

def run_server(port=8765):
    # Ensure upload directory exists
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, AnkiRequestHandler)
    logger.info(f"Starting server on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_server() 