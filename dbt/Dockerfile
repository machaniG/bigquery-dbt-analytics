FROM python:3.11-slim

WORKDIR /usr/app

COPY dbt/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /usr/app

# The actual command is supplied by Cloud Run / Composer.
ENTRYPOINT ["dbt"]