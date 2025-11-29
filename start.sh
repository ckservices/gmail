#!/bin/bash
set -e

# Start Apache in the background
service apache2 start

# Start Flask app with mod_wsgi
# (mod_wsgi will pick up the app via apache.conf)
# Keep the container running
while true; do sleep 1000; done
