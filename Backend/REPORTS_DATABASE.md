# Reports database

The reports flow is designed as:

```text
n8n -> POST /api/internal/reports -> draft
admin review -> POST /api/admin/reports/{id}/publish -> published
React -> GET /api/reports -> published reports only
```

PDF, DOCX, and thumbnail files should be stored in object storage such as S3.
PostgreSQL stores their URLs and report metadata.

## Local PostgreSQL

Start PostgreSQL from the `Backend` directory:

```bash
docker compose up -d postgres
```

Add these values to `Backend/.env`:

```env
DATABASE_URL="postgresql+psycopg://haf:haf-local-only@localhost:5432/haf"
REPORTS_ADMIN_TOKEN="replace-with-a-long-random-token"
```

For a non-Docker database, apply the migration manually:

```bash
psql "$DATABASE_URL" -f migrations/001_create_reports.sql
```

Never use the example password or token in production.

## n8n draft registration

Configure an HTTP Request node:

```text
POST https://api.caifr.com/api/internal/reports
Authorization: Bearer <REPORTS_ADMIN_TOKEN>
Content-Type: application/json
```

Example body:

```json
{
  "external_id": "{{$execution.id}}",
  "title": "Weekly semiconductor report",
  "summary": "Report summary",
  "content": "Report body",
  "thumbnail_url": "https://storage.example.com/thumbnail.png",
  "file_url": "https://storage.example.com/report.pdf",
  "created_by": "n8n"
}
```

`external_id` makes repeated n8n delivery idempotent. New reports always start as
`draft` even if the request contains another status.

## Endpoints

Public:

- `GET /api/reports`
- `GET /api/reports/{report_id}`

Bearer token protected:

- `POST /api/internal/reports`
- `GET /api/admin/reports`
- `PATCH /api/admin/reports/{report_id}`
- `POST /api/admin/reports/{report_id}/publish`
