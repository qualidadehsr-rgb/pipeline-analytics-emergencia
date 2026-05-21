FROM python:3.12-slim

WORKDIR /app

RUN pip install dbt-bigquery==1.11.0 dbt-core==1.11.6

COPY pipeline_analytics/ ./pipeline_analytics/
COPY pipeline_analytics/profiles/profiles.yml ./profiles/profiles.yml

RUN dbt deps --project-dir /app/pipeline_analytics

ENV DBT_PROFILES_DIR=/app/profiles

ENTRYPOINT ["sh", "-c", "dbt run --project-dir /app/pipeline_analytics && dbt test --project-dir /app/pipeline_analytics"]