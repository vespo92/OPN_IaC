version: '3.8'

services:
  web:
    build: .
    container_name: opn_django
    volumes:
      - ./OPN_Django:/app
    ports:
      - "8000:8000"
    environment:
      - DEBUG=True
      - DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
    depends_on:
      - db
    command: bun run start
    restart: unless-stopped

  db:
    image: postgres:14
    container_name: opn_postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=opn_django
    ports:
      - "5432:5432"

volumes:
  postgres_data: