# Deploying to the Cloud

The repository is set up for easy deployment to most Platform-as-a-Service (PaaS) providers like Render, Railway, Fly.io, or Heroku.

## Procfile

The repo includes a `Procfile`, which tells the hosting provider how to run the application:

```
web: gunicorn app:app
```

This uses `gunicorn`, a production-ready web server, to serve the Flask application.

## General Steps

1.  **Create a new Web Service** on your provider of choice, pointing it to your Git repository.
2.  **Set Environment Variables**: In your provider's dashboard, set the required environment variables.
    *   `FLASK_SECRET_KEY`: Set this to a long, random, and unique string.
    *   `DATABASE_URL`: For production, you should use a managed database service (like managed PostgreSQL) and provide its connection URL here. Do not use SQLite in production.
3.  **Build & Deploy**: The provider should automatically detect the `requirements.txt` file and install the dependencies. The `web` process from the `Procfile` will be used to start the server.

## Static Files

By default, Flask serves the static files (CSS, JS, images). For high-traffic applications, you may want to configure a Content Delivery Network (CDN) to serve the `static/` directory for better performance.