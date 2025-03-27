const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const axios = require('axios');

const app = express();
const port = process.env.PORT || 3001;
const ankiConnectUrl = 'http://localhost:8765';

// Path to Anki's collection.media folder (inside the Docker container)
// This is where the .apkg files should be stored
const ankiDataDir = path.join(__dirname, '..', 'anki_data', 'Anki2');

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    // Create Anki data directory if it doesn't exist
    if (!fs.existsSync(ankiDataDir)) {
      fs.mkdirSync(ankiDataDir, { recursive: true });
    }
    cb(null, ankiDataDir);
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname);
  }
});

// File filter to only accept .apkg files
const fileFilter = (req, file, cb) => {
  if (file.mimetype === 'application/octet-stream' || 
      file.originalname.endsWith('.apkg')) {
    cb(null, true);
  } else {
    cb(new Error('Only .apkg files are allowed!'), false);
  }
};

const upload = multer({ 
  storage: storage,
  fileFilter: fileFilter,
  limits: { fileSize: 50 * 1024 * 1024 } // 50MB max file size
});

// Basic middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Create a simple HTML form for uploading files
app.get('/', (req, res) => {
  // Generate the HTML dynamically if index.html doesn't exist
  const html = `
  <!DOCTYPE html>
  <html>
  <head>
    <title>Anki Deck Uploader</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        max-width: 800px;
        margin: 0 auto;
        padding: 20px;
      }
      h1 {
        color: #2c3e50;
      }
      .form-container {
        border: 1px solid #ddd;
        padding: 20px;
        border-radius: 5px;
        margin-top: 20px;
      }
      .form-group {
        margin-bottom: 15px;
      }
      .btn {
        background-color: #3498db;
        color: white;
        padding: 10px 15px;
        border: none;
        border-radius: 4px;
        cursor: pointer;
      }
      .status {
        margin-top: 20px;
        padding: 15px;
        border-radius: 5px;
      }
      .success {
        background-color: #d4edda;
        color: #155724;
      }
      .error {
        background-color: #f8d7da;
        color: #721c24;
      }
    </style>
  </head>
  <body>
    <h1>Anki Deck Uploader</h1>
    <div class="form-container">
      <form action="/upload-deck" method="post" enctype="multipart/form-data">
        <div class="form-group">
          <label for="deck">Select an Anki Deck (.apkg file):</label>
          <input type="file" id="deck" name="deck" accept=".apkg" required>
        </div>
        <button type="submit" class="btn">Upload Deck</button>
      </form>
    </div>
    <div id="status" class="status" style="display: none;"></div>
    
    <script>
      document.querySelector('form').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const statusDiv = document.getElementById('status');
        
        try {
          const response = await fetch('/upload-deck', {
            method: 'POST',
            body: formData
          });
          
          const result = await response.json();
          
          if (response.ok) {
            statusDiv.className = 'status success';
            statusDiv.textContent = \`Success: \${result.message}\`;
          } else {
            statusDiv.className = 'status error';
            statusDiv.textContent = \`Error: \${result.error}\`;
          }
        } catch (error) {
          statusDiv.className = 'status error';
          statusDiv.textContent = \`Error: \${error.message}\`;
        }
        
        statusDiv.style.display = 'block';
      });
    </script>
  </body>
  </html>
  `;
  
  res.send(html);
});

// Endpoint to upload Anki deck (.apkg file)
app.post('/upload-deck', upload.single('deck'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file uploaded or file type not supported' });
    }

    const filePath = req.file.path;
    
    // Optional: Use AnkiConnect to trigger Anki to sync after file upload
    try {
      await axios.post(ankiConnectUrl, {
        action: 'sync',
        version: 6
      });
    } catch (syncError) {
      console.log('Could not trigger Anki sync:', syncError.message);
      // Continue anyway as the file has been uploaded
    }

    return res.status(200).json({ 
      message: 'Deck uploaded successfully',
      file: req.file.originalname,
      path: filePath,
      note: 'The .apkg file has been placed in the Anki data directory. Please open Anki and import the deck manually from File > Import.'
    });
  } catch (error) {
    console.error('Error uploading deck:', error);
    return res.status(500).json({ 
      error: 'Failed to upload deck', 
      details: error.message 
    });
  }
});

// Endpoint to check AnkiConnect status
app.get('/anki-status', async (req, res) => {
  try {
    const response = await axios.post(ankiConnectUrl, {
      action: 'version',
      version: 6
    });
    
    return res.status(200).json({ 
      status: 'connected',
      version: response.data.result
    });
  } catch (error) {
    console.error('Error connecting to AnkiConnect:', error);
    return res.status(500).json({ 
      status: 'disconnected',
      error: error.message 
    });
  }
});

// Start the server
app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
  console.log(`Anki data directory: ${ankiDataDir}`);
}); 