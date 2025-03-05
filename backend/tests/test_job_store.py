"""
Tests for the job store.
"""

import unittest
from unittest.mock import patch, MagicMock
import json
import os
import tempfile
import shutil
from ..infrastructure.job_store import JobStore

class TestJobStore(unittest.TestCase):
    
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a job store with the temporary directory
        self.job_store = JobStore(self.temp_dir)
    
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_create_job(self):
        # Create a job
        job_id = self.job_store.create_job()
        
        # Check that the job ID is a string
        self.assertIsInstance(job_id, str)
        
        # Check that the job file exists
        job_file = os.path.join(self.temp_dir, f"{job_id}.json")
        self.assertTrue(os.path.exists(job_file))
        
        # Check that the job file contains the expected data
        with open(job_file, 'r') as f:
            job_data = json.load(f)
            self.assertEqual(job_data['job_id'], job_id)
            self.assertEqual(job_data['status'], 'pending')
            self.assertEqual(job_data['progress'], 0)
            self.assertIsNone(job_data['result'])
            self.assertIsNone(job_data['error'])
    
    def test_get_job_exists(self):
        # Create a job
        job_id = self.job_store.create_job()
        
        # Get the job
        job = self.job_store.get_job(job_id)
        
        # Check that the job data is correct
        self.assertEqual(job['job_id'], job_id)
        self.assertEqual(job['status'], 'pending')
        self.assertEqual(job['progress'], 0)
        self.assertIsNone(job['result'])
        self.assertIsNone(job['error'])
    
    def test_get_job_not_exists(self):
        # Try to get a non-existent job
        job = self.job_store.get_job('nonexistent-job-id')
        
        # Check that the job is None
        self.assertIsNone(job)
    
    def test_update_job_exists(self):
        # Create a job
        job_id = self.job_store.create_job()
        
        # Update the job
        updated = self.job_store.update_job(
            job_id,
            status='completed',
            progress=100,
            result='Extracted text',
            error=None
        )
        
        # Check that the update was successful
        self.assertTrue(updated)
        
        # Get the job and check that it was updated
        job = self.job_store.get_job(job_id)
        self.assertEqual(job['status'], 'completed')
        self.assertEqual(job['progress'], 100)
        self.assertEqual(job['result'], 'Extracted text')
        self.assertIsNone(job['error'])
    
    def test_update_job_not_exists(self):
        # Try to update a non-existent job
        updated = self.job_store.update_job(
            'nonexistent-job-id',
            status='completed',
            progress=100,
            result='Extracted text',
            error=None
        )
        
        # Check that the update failed
        self.assertFalse(updated)
    
    def test_delete_job_exists(self):
        # Create a job
        job_id = self.job_store.create_job()
        
        # Delete the job
        deleted = self.job_store.delete_job(job_id)
        
        # Check that the deletion was successful
        self.assertTrue(deleted)
        
        # Check that the job file no longer exists
        job_file = os.path.join(self.temp_dir, f"{job_id}.json")
        self.assertFalse(os.path.exists(job_file))
        
        # Try to get the job and check that it's None
        job = self.job_store.get_job(job_id)
        self.assertIsNone(job)
    
    def test_delete_job_not_exists(self):
        # Try to delete a non-existent job
        deleted = self.job_store.delete_job('nonexistent-job-id')
        
        # Check that the deletion failed
        self.assertFalse(deleted)
    
    def test_list_jobs(self):
        # Create multiple jobs
        job_ids = [self.job_store.create_job() for _ in range(3)]
        
        # List all jobs
        jobs = self.job_store.list_jobs()
        
        # Check that all jobs are in the list
        self.assertEqual(len(jobs), 3)
        for job in jobs:
            self.assertIn(job['job_id'], job_ids)
    
    def test_cleanup_old_jobs(self):
        # Create jobs with different timestamps
        job_ids = []
        for i in range(5):
            job_id = self.job_store.create_job()
            job_ids.append(job_id)
            
            # Manually set the timestamp to simulate old jobs
            job_file = os.path.join(self.temp_dir, f"{job_id}.json")
            with open(job_file, 'r') as f:
                job_data = json.load(f)
            
            # Set timestamp to be older for the first 3 jobs
            if i < 3:
                job_data['timestamp'] = 0  # Very old timestamp
            
            with open(job_file, 'w') as f:
                json.dump(job_data, f)
        
        # Clean up old jobs (older than current time)
        cleaned_count = self.job_store.cleanup_old_jobs(max_age_seconds=1)
        
        # Check that 3 jobs were cleaned up
        self.assertEqual(cleaned_count, 3)
        
        # Check that only the newer jobs remain
        remaining_jobs = self.job_store.list_jobs()
        self.assertEqual(len(remaining_jobs), 2)
        for job in remaining_jobs:
            self.assertIn(job['job_id'], job_ids[3:])

if __name__ == '__main__':
    unittest.main()