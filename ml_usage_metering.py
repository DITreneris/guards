#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ML Usage Metering

This module handles tracking, billing, and resource usage metering for the ML system.
It's a crucial component for commercialization, enabling proper billing and usage tracking.
"""

import os
import json
import time
import uuid
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from contextlib import contextmanager

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define constants
METERING_DATA_DIR = Path("data/metering")
DEFAULT_STORAGE_PATH = METERING_DATA_DIR / "usage_data.json"
LOCK_TIMEOUT = 10  # seconds

class UsageMetric:
    """Represents a type of usage that can be metered"""
    API_CALL = "api_call"
    MODEL_INFERENCE = "model_inference"
    MODEL_TRAINING = "model_training"
    DATA_STORAGE = "data_storage"
    DATA_TRANSFER = "data_transfer"

class MeteringRecord:
    """Individual usage record"""
    def __init__(
        self,
        client_id: str,
        metric_type: str,
        value: float = 1.0,
        timestamp: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.id = str(uuid.uuid4())
        self.client_id = client_id
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary for serialization"""
        return {
            "id": self.id,
            "client_id": self.client_id,
            "metric_type": self.metric_type,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MeteringRecord':
        """Create record from dictionary representation"""
        record = cls(
            client_id=data["client_id"],
            metric_type=data["metric_type"],
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {})
        )
        record.id = data["id"]
        return record

class FileLock:
    """Simple file-based lock for coordinating access to shared resources"""
    def __init__(self, lock_file: Union[str, Path]):
        self.lock_file = Path(lock_file)
        self.timeout = LOCK_TIMEOUT
    
    def acquire(self) -> bool:
        """Acquire the lock"""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            try:
                self.lock_file.parent.mkdir(parents=True, exist_ok=True)
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode('utf-8'))
                os.close(fd)
                return True
            except FileExistsError:
                # Lock exists, check if it's stale
                try:
                    lock_age = time.time() - os.path.getctime(self.lock_file)
                    if lock_age > self.timeout:
                        # Stale lock, try to remove it
                        os.unlink(self.lock_file)
                        continue
                except (FileNotFoundError, PermissionError):
                    pass
                
                # Wait and retry
                time.sleep(0.1)
        
        logger.error(f"Could not acquire lock on {self.lock_file} after {self.timeout} seconds")
        return False
    
    def release(self) -> bool:
        """Release the lock"""
        try:
            os.unlink(self.lock_file)
            return True
        except (FileNotFoundError, PermissionError) as e:
            logger.error(f"Error releasing lock: {e}")
            return False

class UsageMeter:
    """Tracks and stores usage metrics for billing purposes"""
    def __init__(
        self, 
        storage_path: Union[str, Path] = DEFAULT_STORAGE_PATH,
        use_redis: bool = False,
        redis_url: Optional[str] = None
    ):
        self.storage_path = Path(storage_path)
        self.use_redis = use_redis and REDIS_AVAILABLE
        self.redis_client = None
        self.lock_path = self.storage_path.with_suffix(".lock")
        
        if self.use_redis:
            try:
                self.redis_client = redis.from_url(redis_url or "redis://localhost:6379/0")
                self.redis_client.ping()  # Test connection
                logger.info("Redis connection established for usage metering")
            except (redis.ConnectionError, redis.RedisError) as e:
                logger.warning(f"Redis connection failed: {e}. Falling back to file storage.")
                self.use_redis = False
                self.redis_client = None
        
        # Ensure storage directory exists
        if not self.use_redis:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            logger.info(f"Usage metering configured with file storage at {self.storage_path}")
    
    def _get_lock(self) -> FileLock:
        """Get a lock object for this storage path"""
        return FileLock(self.lock_path)
    
    @contextmanager
    def _with_lock(self):
        """Context manager for file locking"""
        lock = self._get_lock()
        try:
            if lock.acquire():
                yield
            else:
                raise RuntimeError("Failed to acquire lock for usage metering")
        finally:
            lock.release()
    
    def record_usage(self, client_id: str, metric_type: str, value: float = 1.0, 
                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Record a usage metric
        
        Args:
            client_id: Identifier for the client/account
            metric_type: Type of usage (see UsageMetric class)
            value: Numeric value of usage (e.g., 1.0 for API call, file size in MB, etc.)
            metadata: Additional information about the usage
            
        Returns:
            ID of the created record
        """
        record = MeteringRecord(
            client_id=client_id,
            metric_type=metric_type,
            value=value,
            metadata=metadata
        )
        
        if self.use_redis:
            try:
                # Store in Redis
                self.redis_client.hset(
                    f"usage:{client_id}:{record.id}",
                    mapping=record.to_dict()
                )
                # Add to time-series index
                self.redis_client.zadd(
                    f"usage_timeline:{client_id}",
                    {record.id: record.timestamp.timestamp()}
                )
                # Add to metric type index
                self.redis_client.sadd(
                    f"usage_metric:{client_id}:{metric_type}",
                    record.id
                )
                logger.debug(f"Recorded usage in Redis: {client_id}, {metric_type}, {value}")
                return record.id
            except Exception as e:
                logger.error(f"Error recording usage in Redis: {e}")
                # Fall back to file storage
        
        # File storage logic
        try:
            with self._with_lock():
                data = self._load_data()
                
                if client_id not in data:
                    data[client_id] = []
                
                data[client_id].append(record.to_dict())
                self._save_data(data)
            
            logger.debug(f"Recorded usage: {client_id}, {metric_type}, {value}")
            return record.id
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            raise
    
    def _load_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load usage data from storage"""
        if not self.storage_path.exists():
            return {}
        
        try:
            with open(self.storage_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding usage data from {self.storage_path}, starting fresh")
            return {}
    
    def _save_data(self, data: Dict[str, List[Dict[str, Any]]]):
        """Save usage data to storage"""
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_usage(self, client_id: str, 
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  metric_type: Optional[str] = None) -> List[MeteringRecord]:
        """
        Get usage records for a client
        
        Args:
            client_id: Client identifier
            start_time: Optional start time for filtering
            end_time: Optional end time for filtering
            metric_type: Optional metric type for filtering
            
        Returns:
            List of usage records
        """
        if self.use_redis:
            try:
                # Get record IDs based on filters
                if metric_type:
                    record_ids = self.redis_client.smembers(f"usage_metric:{client_id}:{metric_type}")
                else:
                    # Get from timeline with time range
                    min_score = start_time.timestamp() if start_time else "-inf"
                    max_score = end_time.timestamp() if end_time else "+inf"
                    record_ids = self.redis_client.zrangebyscore(
                        f"usage_timeline:{client_id}",
                        min_score, max_score
                    )
                
                # Get record details
                records = []
                for record_id in record_ids:
                    if isinstance(record_id, bytes):
                        record_id = record_id.decode('utf-8')
                    
                    record_data = self.redis_client.hgetall(f"usage:{client_id}:{record_id}")
                    if record_data:
                        # Convert bytes to strings if necessary
                        record_dict = {
                            k.decode('utf-8') if isinstance(k, bytes) else k: 
                            v.decode('utf-8') if isinstance(v, bytes) else v
                            for k, v in record_data.items()
                        }
                        
                        # Convert string fields to appropriate types
                        if 'value' in record_dict:
                            record_dict['value'] = float(record_dict['value'])
                        
                        if 'metadata' in record_dict and isinstance(record_dict['metadata'], str):
                            record_dict['metadata'] = json.loads(record_dict['metadata'])
                        
                        record = MeteringRecord.from_dict(record_dict)
                        
                        # Apply time filtering if needed
                        if ((not start_time or record.timestamp >= start_time) and
                            (not end_time or record.timestamp <= end_time)):
                            records.append(record)
                
                return records
            except Exception as e:
                logger.error(f"Error retrieving usage from Redis: {e}")
                # Fall back to file storage
        
        # File storage logic
        try:
            with self._with_lock():
                data = self._load_data()
                
                if client_id not in data:
                    return []
                
                records = []
                for record_dict in data[client_id]:
                    record = MeteringRecord.from_dict(record_dict)
                    
                    # Apply filters
                    if metric_type and record.metric_type != metric_type:
                        continue
                    
                    if start_time and record.timestamp < start_time:
                        continue
                    
                    if end_time and record.timestamp > end_time:
                        continue
                    
                    records.append(record)
                
                return records
        except Exception as e:
            logger.error(f"Error retrieving usage: {e}")
            raise
    
    def get_usage_summary(self, client_id: str, 
                         period_start: Optional[datetime] = None,
                         period_end: Optional[datetime] = None) -> Dict[str, float]:
        """
        Get a summary of usage by metric type for a given period
        
        Args:
            client_id: Client identifier
            period_start: Start of the billing period
            period_end: End of the billing period
            
        Returns:
            Dictionary with metric types as keys and total usage as values
        """
        # Default to current month if not specified
        if not period_start:
            today = datetime.now()
            period_start = datetime(today.year, today.month, 1)
        
        if not period_end:
            period_end = datetime.now()
        
        records = self.get_usage(
            client_id=client_id,
            start_time=period_start,
            end_time=period_end
        )
        
        summary = {}
        for record in records:
            if record.metric_type not in summary:
                summary[record.metric_type] = 0
            
            summary[record.metric_type] += record.value
        
        return summary

    def calculate_billing(self, client_id: str, tier: str, 
                         period_start: Optional[datetime] = None,
                         period_end: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate billing for a client based on usage
        
        Args:
            client_id: Client identifier
            tier: Pricing tier (basic, professional, enterprise)
            period_start: Start of the billing period
            period_end: End of the billing period
            
        Returns:
            Dictionary with billing information
        """
        from ml_sales_config import get_sales_config
        
        # Get pricing tier
        config = get_sales_config()
        if tier not in config.pricing_tiers:
            raise ValueError(f"Unknown pricing tier: {tier}")
        
        tier_config = config.pricing_tiers[tier]
        
        # Default to current month if not specified
        if not period_start:
            today = datetime.now()
            period_start = datetime(today.year, today.month, 1)
        
        if not period_end:
            period_end = datetime.now()
        
        # Get usage summary
        summary = self.get_usage_summary(
            client_id=client_id,
            period_start=period_start,
            period_end=period_end
        )
        
        # Base price
        price = tier_config.price_monthly
        
        # Check if any usage exceeds limits
        overage_charges = {}
        
        # API call overage
        api_calls = summary.get(UsageMetric.API_CALL, 0)
        # Calculate API call limit based on rate limit over the whole period
        period_duration = (period_end - period_start).total_seconds() / 60  # in minutes
        api_call_limit = tier_config.api_rate_limit * period_duration
        
        if api_calls > api_call_limit:
            overage = api_calls - api_call_limit
            # Charge $0.01 per excess API call
            overage_charges["api_calls"] = overage * 0.01
        
        # Model inference overage
        model_inferences = summary.get(UsageMetric.MODEL_INFERENCE, 0)
        # For simplicity, assume 10,000 inferences included
        if model_inferences > 10000:
            overage = model_inferences - 10000
            # Charge $0.001 per excess inference
            overage_charges["model_inference"] = overage * 0.001
        
        # Data storage overage
        data_storage = summary.get(UsageMetric.DATA_STORAGE, 0)  # in MB
        # Assume 1GB (1024 MB) included
        if data_storage > 1024:
            overage = data_storage - 1024
            # Charge $0.05 per excess MB
            overage_charges["data_storage"] = overage * 0.05
        
        # Calculate total
        total_overage = sum(overage_charges.values())
        total_price = price + total_overage
        
        return {
            "client_id": client_id,
            "tier": tier,
            "period_start": period_start.isoformat() if period_start else None,
            "period_end": period_end.isoformat() if period_end else None,
            "base_price": price,
            "usage_summary": summary,
            "overage_charges": overage_charges,
            "total_overage": total_overage,
            "total_price": total_price
        }

class MeteringMiddleware:
    """Middleware for tracking API usage in web frameworks"""
    
    def __init__(self, meter: UsageMeter, get_client_id_func):
        """
        Initialize the middleware
        
        Args:
            meter: UsageMeter instance
            get_client_id_func: Function that extracts client ID from request
        """
        self.meter = meter
        self.get_client_id_func = get_client_id_func
    
    def __call__(self, request):
        """Process the request and track usage"""
        # This is a generic implementation - extend for your web framework
        client_id = self.get_client_id_func(request)
        
        if not client_id:
            # Skip metering if client ID can't be determined
            return request
        
        # Record API usage
        endpoint = getattr(request, 'endpoint', 'unknown')
        self.meter.record_usage(
            client_id=client_id,
            metric_type=UsageMetric.API_CALL,
            metadata={
                "endpoint": endpoint,
                "method": getattr(request, 'method', 'unknown'),
                "ip": getattr(request, 'remote_addr', 'unknown')
            }
        )
        
        return request

# FLASK specific middleware
def create_flask_metering_middleware(app, meter: UsageMeter, get_client_id_func):
    """Create a Flask-specific middleware for metering"""
    @app.before_request
    def before_request():
        from flask import request
        client_id = get_client_id_func(request)
        
        if not client_id:
            return None
        
        meter.record_usage(
            client_id=client_id,
            metric_type=UsageMetric.API_CALL,
            metadata={
                "endpoint": request.endpoint,
                "method": request.method,
                "ip": request.remote_addr
            }
        )
        
        return None

def print_usage_report(client_id: str, days: int = 30):
    """Print a usage report for a client"""
    meter = UsageMeter()
    
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    
    usage = meter.get_usage(
        client_id=client_id,
        start_time=start_time,
        end_time=end_time
    )
    
    summary = {}
    for record in usage:
        if record.metric_type not in summary:
            summary[record.metric_type] = 0
        
        summary[record.metric_type] += record.value
    
    print(f"\n=== USAGE REPORT FOR {client_id} ({days} days) ===\n")
    
    if not summary:
        print("No usage recorded in this period.")
        return
    
    for metric, value in summary.items():
        print(f"{metric}: {value:.2f}")
    
    # Calculate billing for each tier
    print("\n=== BILLING ESTIMATES ===\n")
    
    for tier in ["basic", "professional", "enterprise"]:
        try:
            billing = meter.calculate_billing(
                client_id=client_id,
                tier=tier,
                period_start=start_time,
                period_end=end_time
            )
            
            print(f"{tier.capitalize()} Tier:")
            print(f"  Base Price: ${billing['base_price']:.2f}")
            
            if billing['overage_charges']:
                print(f"  Overage Charges:")
                for charge_type, amount in billing['overage_charges'].items():
                    print(f"    {charge_type}: ${amount:.2f}")
            
            print(f"  Total: ${billing['total_price']:.2f}")
            print()
        except Exception as e:
            logger.error(f"Error calculating billing for {tier} tier: {e}")

def main():
    """Main function for command-line usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="ML Usage Metering Tool")
    parser.add_argument('--report', type=str, help='Generate usage report for client ID')
    parser.add_argument('--days', type=int, default=30, help='Number of days for report')
    parser.add_argument('--record', type=str, help='Record usage for client ID')
    parser.add_argument('--metric', type=str, help='Metric type for recording')
    parser.add_argument('--value', type=float, default=1.0, help='Value for recording')
    args = parser.parse_args()
    
    if args.report:
        print_usage_report(args.report, args.days)
    
    if args.record and args.metric:
        meter = UsageMeter()
        record_id = meter.record_usage(
            client_id=args.record,
            metric_type=args.metric,
            value=args.value
        )
        print(f"Recorded usage: {record_id}")

if __name__ == "__main__":
    main() 