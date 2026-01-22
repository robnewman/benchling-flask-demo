FROM public.ecr.aws/docker/library/python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080
CMD ["python3", "-m", "gunicorn", "local_app.app:app", "--bind", "0.0.0.0:8080"]