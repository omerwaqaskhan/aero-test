# Celery Background Jobs Setup

This document describes the Celery setup for handling background tasks in the LuftWay Travel Platform.

## Overview

Celery is used to handle asynchronous tasks that should not block HTTP requests:
- **Email sending** (verification, password reset, notifications)
- **Data scraping** (hotel data collection, price updates)
- **Cache warming** (pre-loading frequently accessed data)
- **Report generation** (analytics, exports)

## Architecture

- **Broker**: Redis (message queue)
- **Backend**: Redis (result storage)
- **Workers**: Separate Celery worker processes
- **Monitoring**: Flower (web-based monitoring tool)

## Installation

Celery is already included in `requirements.txt`. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

## Running Celery Workers

### Development

```bash
# Start Celery worker
celery -A auth_module.core.celery_app worker --loglevel=info

# Start worker for specific queue
celery -A auth_module.core.celery_app worker --loglevel=info -Q emails
celery -A auth_module.core.celery_app worker --loglevel=info -Q scraping
```

### Production (Docker)

Add to `docker-compose.yml`:

```yaml
celery_worker:
  build: ./backend
  command: celery -A auth_module.core.celery_app worker --loglevel=info
  volumes:
    - ./backend:/app
  environment:
    - DATABASE_URL=${DATABASE_URL}
    - REDIS_URL=${REDIS_URL}
  depends_on:
    - postgres
    - redis
```

## Monitoring with Flower

Flower provides a web-based interface for monitoring Celery tasks.

### Start Flower

```bash
celery -A auth_module.core.celery_app flower --port=5555
```

Then open http://localhost:5555 in your browser.

### Docker Compose

```yaml
flower:
  build: ./backend
  command: celery -A auth_module.core.celery_app flower --port=5555
  ports:
    - "5555:5555"
  environment:
    - REDIS_URL=${REDIS_URL}
  depends_on:
    - redis
```

## Using Tasks in Code

### Email Tasks

```python
from auth_module.tasks.email_tasks import send_email_async

# Send email asynchronously
send_email_async.delay(
    to_email="user@example.com",
    subject="Welcome!",
    html_content="<h1>Welcome</h1>",
    text_content="Welcome"
)
```

### Scraping Tasks

```python
from search_booking_module.tasks.scraping_tasks import scrape_hotel_data_async

# Scrape hotels asynchronously
scrape_hotel_data_async.delay(
    destination="Paris",
    max_hotels=50
)
```

## Task Queues

Tasks are routed to different queues based on priority:

- **emails**: Email sending tasks
- **scraping**: Data scraping tasks
- **cache**: Cache warming tasks
- **default**: General tasks

## Configuration

Celery configuration is in `auth_module/core/celery_app.py`:

- **Task time limits**: 30 minutes max, 25 minutes soft limit
- **Retry policy**: 3 retries with exponential backoff
- **Worker settings**: Prefetch multiplier, max tasks per child

## Best Practices

1. **Always use `.delay()` or `.apply_async()`** - Never call tasks directly
2. **Handle failures gracefully** - Tasks have retry logic built-in
3. **Monitor task queues** - Use Flower to watch for stuck tasks
4. **Scale workers** - Add more workers for high-load queues
5. **Use appropriate queues** - Route tasks to dedicated queues

## Troubleshooting

### Tasks not executing

1. Check worker is running: `celery -A auth_module.core.celery_app inspect active`
2. Check Redis connection: `redis-cli ping`
3. Check logs: `celery -A auth_module.core.celery_app worker --loglevel=debug`

### Tasks failing

1. Check task logs in Flower
2. Verify dependencies (database, external APIs)
3. Check task time limits (may need adjustment)

### High memory usage

1. Reduce `worker_prefetch_multiplier`
2. Lower `worker_max_tasks_per_child`
3. Add more workers instead of increasing prefetch

