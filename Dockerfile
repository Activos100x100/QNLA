FROM python:3.11

WORKDIR /app

# Copy only minimal requirements for faster builds
COPY requirements-minimal.txt requirements-minimal.txt

RUN pip install --no-cache-dir -r requirements-minimal.txt

COPY . .

EXPOSE 8080

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]