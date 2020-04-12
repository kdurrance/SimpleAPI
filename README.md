# SimpleAPI
Simple API to expose host hardware information. Requires psutil and istats (macOS)

API requires authentication via a simple api_key, configurable in code or passed on the command line

Supported request URLs:
http://localhost:8008/api/1.0/cpu?api_key=[apikeytext]
http://localhost:8008/api/1.0/mem?api_key=[apikeytext]
http://localhost:8008/api/1.0/disk?api_key=[apikeytext]
http://localhost:8008/api/1.0/sensor?api_key=[apikeytext]
http://localhost:8008/api/1.0/network?api_key=[apikeytext]
