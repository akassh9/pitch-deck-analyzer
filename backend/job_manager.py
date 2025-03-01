# backend/job_manager.py
import os
import redis
import json
import uuid

# Read REDIS_URL from environment variables; if not provided, default to localhost.
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(redis_url)

def create_job(expiration=3600):
    job_id = str(uuid.uuid4())
    job_data = {"status": "pending", "result": None, "progress": 0}
    redis_client.setex(f"job:{job_id}", expiration, json.dumps(job_data))
    return job_id

def update_job(job_id, data, expiration=3600):
    key = f"job:{job_id}"
    current_data = redis_client.get(key)
    if current_data:
        job_data = json.loads(current_data)
        job_data.update(data)
        redis_client.setex(key, expiration, json.dumps(job_data))

def get_job(job_id):
    key = f"job:{job_id}"
    job = redis_client.get(key)
    return json.loads(job) if job else None

def delete_job(job_id):
    key = f"job:{job_id}"
    redis_client.delete(key)