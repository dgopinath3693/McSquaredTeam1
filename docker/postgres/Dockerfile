FROM postgres:15-alpine

# Copy initialization SQL into the docker-entrypoint init dir
COPY init-db.sql /docker-entrypoint-initdb.d/init-db.sql

# Expose default postgres port
EXPOSE 5432
