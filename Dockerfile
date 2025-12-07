FROM python:3.10

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the rest of the app
COPY . /app

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]