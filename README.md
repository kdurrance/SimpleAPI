# SimpleAPI
Simple API to expose host hardware information. Requires psutil and istats (macOS)

API requires authentication via a simple api_key, which autogenerates on start, creating an "api.key" file in the same directory as the running script.

# Running the server
Optional command line parameters of (1) TCP Port number, defaults to port 8008 if no argument is passed. 

Python3 ./APIserver.py [8008]

# Supported request URLs:
- http://localhost:8008/api/1.0/cpu?api_key=[apikeytext]
- http://localhost:8008/api/1.0/mem?api_key=[apikeytext]
- http://localhost:8008/api/1.0/disk?api_key=[apikeytext]
- http://localhost:8008/api/1.0/sensor?api_key=[apikeytext]
- http://localhost:8008/api/1.0/network?api_key=[apikeytext]
