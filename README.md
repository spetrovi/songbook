# songbook

dnf install lilypond -y
pip install -r requirements.txt

uvicorn app.main:app --reload


### Run it containerized

```bash
podman build -t songbook:latest .
```

```bash
podman pod create --name songbook_pod -p 8000:8000
podman run -d \
    --pod songbook_pod \
    --name songbook_db \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_DB=postgres \
    postgres:16
podman run -d \
    --pod songbook_pod \
    --name songbook_app \
    -e DATABASE_SCHEMA=postgres \
    -e DATABASE_USER=postgres \
    -e DATABASE_PASSWORD=postgres \
    -e DATABASE_NAME=postgres \
    -e secret_key=secret \
    -e register_enabled=true \
    -v /tmp/songbook:/code/app/tmp:Z \
    songbook:latest
```
