
FROM python:2.7 as app

WORKDIR /app

COPY requirements.txt ./
COPY server.py ./
COPY templates ./templates

RUN pip install --no-cache-dir -r requirements.txt

WORKDIR /app

FROM docker.io/keinos/sqlite3:latest as db_builder
WORKDIR /app

COPY schema.sql .
COPY tests/api/test_data.sql test_data.sql

# Set up test database
USER root
RUN sqlite3 test.db < schema.sql
RUN sqlite3 test.db < test_data.sql

# Use official Hurl image
FROM app as test_app
COPY --from=db_builder /app/test.db /app/test.db
WORKDIR /app

COPY tests/server.cfg .
COPY tests/api ./tests/api


CMD ["bash", "tests/api/run_tests.sh", "server_only"]

# Copy test files
from test_app as hurl_tests
COPY --from=ghcr.io/orange-opensource/hurl:latest / /
# Run API tests
# CMD ["python", "./server.py"]
CMD ["bash", "tests/api/run_tests.sh"]

