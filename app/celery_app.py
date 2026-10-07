from celery import Celery

celery = Celery(
    "certificate_generator",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0",
    include=["app.tasks"]
)