const express = require('express');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const axios = require('axios');
const logger = require('./logger');

const app = express();
const port = process.env.PORT || 3000;
const ankiConnectUrl = 'http://localhost:8765';

// Path to store imported decks
const importDir = path.join(__dirname, '..', 'anki_data', 'imports');

// Ensure import directory exists
if (!fs.existsSync(importDir)) {
  fs.mkdirSync(importDir, { recursive: true });
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    cb(null, importDir);
  },
  filename: (req, file, cb) => {
    cb(null, file.originalname);
  }
});

const fileFilter = (req, file, cb) => {
  if (file.originalname.endsWith('.apkg')) {
    cb(null, true);
  } else {
    cb(new Error('Only .apkg files are allowed!'), false);
  }
};

const upload = multer({ 
  storage: storage,
  fileFilter: fileFilter,
  limits: { fileSize: 50 * 1024 * 1024 }
});

app.use(express.json());

app.get('/anki-connect-status', async (req, res) => {
  try {
    const response = await axios.post(ankiConnectUrl, {});
    logger.info('AnkiConnect status check successful');
    return res.status(200).json({ 
      status: 'connected',
      version: response.data.result
    });
  } catch (error) {
    logger.error('AnkiConnect connection failed', { error: error.message });
    return res.status(500).json({ 
      status: 'disconnected',
      error: error.message 
    });
  }
});

app.post('/uploadDeck', upload.single('deck'), async (req, res) => {
  try {
    if (!req.file) {
      logger.warn('Upload attempt with no file or invalid file type');
      return res.status(400).json({ error: 'No file uploaded or invalid file type' });
    }

    const filePath = req.file.path;
    logger.info('Deck file received', { filename: req.file.originalname, path: filePath });
    
    const response = await axios.post(ankiConnectUrl, {
      action: 'importPackage',
      version: 6,
      params: {
        path: filePath
      }
    });

    if (response.data.result !== true) {
      logger.error('Anki import failed', { 
        filename: req.file.originalname, 
        error: response.data.error 
      });

      // Delete the file if import fails
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath);
        logger.info('Failed import file deleted', { path: filePath });
      }
      return res.status(500).json({ 
        error: 'Failed to import deck', 
        details: response.data.error
      });
    }

    logger.info('Deck imported successfully', { filename: req.file.originalname });
    return res.status(200).json({ 
      message: 'Deck imported successfully',
      file: req.file.originalname
    });
  } catch (error) {
    logger.error('Unexpected error during deck import', { 
      error: error.message,
      stack: error.stack
    });
    return res.status(500).json({ 
      error: 'Failed to import deck', 
      details: error.message 
    });
  }
});

app.get('/exportDeck/:deckName', async (req, res) => {
  const deckName = req.params.deckName;
  const exportPath = path.join(importDir, `${deckName}.apkg`);

  logger.info('Export deck requested', { deckName, exportPath });

  try {
    const response = await axios.post(ankiConnectUrl, {
      action: 'exportPackage',
      version: 6,
      params: {
        deck: deckName,
        path: exportPath,
        includeSched: true
      }
    });

    if (!fs.existsSync(exportPath)) {
      logger.error('Requested deck file does not exist', { deckName, exportPath });
      return res.status(404).json({ error: 'Requested deck file not found' });
    }

    logger.info('Starting file download', { deckName, exportPath });
    res.download(exportPath, path.basename(exportPath));

    // Only delete on successful transfer
    res.on('finish', () => {
      if (fs.existsSync(exportPath)) {
        fs.unlinkSync(exportPath);
        logger.info('File successfully transferred and deleted', { path: exportPath });
      }
    });

    // Just log the error but don't delete the file if transfer fails
    res.on('error', (err) => {
      logger.error('Error during file download', { error: err.message, path: exportPath });
    });
  } catch (error) {
    logger.error('Error exporting deck', { 
      error: error.message, 
      stack: error.stack,
      deckName 
    });
    return res.status(500).json({ 
      error: 'Failed to export deck', 
      details: error.message 
    });
  }
});

app.listen(port, () => {
  logger.info('Server started', { 
    port, 
    importDir,
    environment: process.env.NODE_ENV || 'development'
  });
}); 