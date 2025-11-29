# Use official Python image
FROM python:3.10-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Flask
EXPOSE 5000

# For Apache mod_wsgi
RUN apt-get update && apt-get install -y apache2 apache2-utils libapache2-mod-wsgi-py3 && rm -rf /var/lib/apt/lists/*

COPY apache.conf /etc/apache2/sites-available/000-default.conf

# Start script
CMD ["/bin/bash", "start.sh"]
