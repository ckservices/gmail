FROM python:3.10

WORKDIR /app
COPY . /app

RUN apt-get update && apt-get install -y build-essential apache2-dev
RUN pip install --no-cache-dir -r requirements.txt

# Expose port for Flask
EXPOSE 5000

CMD ["python", "app.py"]