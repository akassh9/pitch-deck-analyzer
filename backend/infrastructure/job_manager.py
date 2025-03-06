"""
Job management utilities for handling asynchronous processing tasks.
This module provides functions to create, update, retrieve, and delete jobs
stored in Redis.
"""

import os
import redis
import json
import uuid
import logging
from datetime import datetime
from ..utils.error_handling import ResourceNotFoundError

logger = logging.getLogger(__name__)

class JobManager:
    """Manager for handling job lifecycle in Redis."""
    
    def __init__(self, config):
        """Initialize the job manager with configuration."""
        self.config = config
        redis_url = f"redis://{config.REDIS_HOST}:{config.REDIS_PORT}/{config.REDIS_DB}"
        self.redis_client = redis.from_url(redis_url)
        logger.info(f"Initialized JobManager with Redis at {redis_url}")
    
    def create_job(self, expiration=3600, metadata=None):
        """
        Create a new job in Redis.
        
        Args:
            expiration (int): Time in seconds until the job expires
            metadata (dict): Optional metadata to store with the job
            
        Returns:
            str: The job ID
        """
        job_id = str(uuid.uuid4())
        job_data = {
            "id": job_id,
            "status": "pending",
            "result": None,
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        key = f"job:{job_id}"
        self.redis_client.setex(key, expiration, json.dumps(job_data))
        logger.debug(f"Created job {job_id}")
        
        return job_id
    
    def update_job(self, job_id, data, expiration=3600):
        """
        Update an existing job in Redis.
        
        Args:
            job_id (str): The job ID
            data (dict): Data to update in the job
            expiration (int): Time in seconds until the job expires
            
        Raises:
            ResourceNotFoundError: If the job does not exist
        """
        key = f"job:{job_id}"
        current_data = self.redis_client.get(key)
        
        if not current_data:
            logger.warning(f"Attempted to update non-existent job {job_id}")
            raise ResourceNotFoundError("Job", job_id)
            
        job_data = json.loads(current_data)
        job_data.update(data)
        job_data["updated_at"] = datetime.now().isoformat()
        
        self.redis_client.setex(key, expiration, json.dumps(job_data))
        logger.debug(f"Updated job {job_id}: {data.keys()}")
    
    def get_job(self, job_id):
        """
        Get a job from Redis.
        
        Args:
            job_id (str): The job ID
            
        Returns:
            dict: The job data, or None if the job does not exist
        """
        key = f"job:{job_id}"
        job = self.redis_client.get(key)
        
        if not job:
            logger.debug(f"Job {job_id} not found")
            return None
            
        return json.loads(job)
    
    def delete_job(self, job_id):
        """
        Delete a job from Redis.
        
        Args:
            job_id (str): The job ID
        """
        key = f"job:{job_id}"
        result = self.redis_client.delete(key)
        
        if result:
            logger.debug(f"Deleted job {job_id}")
        else:
            logger.debug(f"Attempted to delete non-existent job {job_id}")

# Create a singleton instance
_job_manager = None

def get_job_manager(config=None):
    """Get the singleton JobManager instance."""
    global _job_manager
    
    if _job_manager is None:
        from ..config import Config
        _job_manager = JobManager(config or Config)
        
    return _job_manager

# Convenience functions that use the singleton
def create_job(expiration=3600, metadata=None):
    """Create a new job."""
    return get_job_manager().create_job(expiration, metadata)

def update_job(job_id, data, expiration=3600):
    """Update an existing job."""
    return get_job_manager().update_job(job_id, data, expiration)

def get_job(job_id):
    """Get a job."""
    return get_job_manager().get_job(job_id)

def delete_job(job_id):
    """Delete a job."""
    return get_job_manager().delete_job(job_id) 