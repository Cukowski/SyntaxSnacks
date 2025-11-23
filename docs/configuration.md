# Configuration

Configuration is managed via environment variables, typically loaded from a `.env` file in local development. You can copy the example file to get started:

```bash
cp .env.example .env
```

| Key                | Default            | Description                                                              |
| ------------------ | ------------------ | ------------------------------------------------------------------------ |
| `FLASK_SECRET_KEY` | `dev-secret`       | A strong, unique secret key for signing session cookies. **Change this!**  |
| `DATABASE_URL`     | `sqlite:///app.db` | The full SQLAlchemy connection string for your database.                 |

## Database Examples

```ini
# SQLite (default for local development)
DATABASE_URL=sqlite:///app.db

# PostgreSQL (recommended for production)
DATABASE_URL=postgresql+psycopg2://user:pass@host:5432/dbname
```