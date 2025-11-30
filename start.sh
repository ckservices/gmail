
#!/bin/bash
set -e

# Start Flask app with Gunicorn
exec gunicorn --bind 0.0.0.0:5000 app:app
