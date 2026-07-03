FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir ".[web]" gunicorn

EXPOSE 5421

CMD ["gunicorn", "-w", "2", "--timeout", "300", "-b", "0.0.0.0:5421", "schedule_parser.web:create_app()"]
