# syntax=docker/dockerfile:1
FROM python:3.13-slim

WORKDIR /code

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Run migrations and start server
CMD ["/bin/sh", "-c", "python movie_picker/manage.py migrate && python movie_picker/manage.py runserver 0.0.0.0:8000"]
