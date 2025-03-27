# AnkiConnect Configuration

This directory contains the AnkiConnect addon configuration. The `config.json` file is essential for the addon to function properly.

## Configuration

The `config.json` file is automatically configured with the following settings:
```json
{
    "apiKey": null,
    "apiLogPath": null,
    "ignoreOriginList": [],
    "webBindAddress": "0.0.0.0",
    "webBindPort": 8765,
    "webCorsOrigin": "http://localhost",
    "webCorsOriginList": ["*"]
}
```

The configuration is automatically copied to the correct location during container startup, and no manual steps are required.

## Important Notes

- The `webBindAddress` is set to "0.0.0.0" to accept connections from any interface
- The `webBindPort` is set to 8765 (default AnkiConnect port)
- CORS is configured to allow connections from localhost
- The configuration is preserved across container restarts 