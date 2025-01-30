import logging
import time
import uuid

import redis

from rest_framework.authentication import TokenAuthentication
from rest_framework.exceptions import PermissionDenied
from django.conf import settings

LOG = logging.getLogger("fuzzmanager.utils")


class RedisLock:
    """Simple Redis mutex lock.

    based on: https://redislabs.com/ebook/part-2-core-concepts \
              /chapter-6-application-components-in-redis/6-2-distributed-locking \
              /6-2-3-building-a-lock-in-redis/

    Not using RedLock because it isn't passable as a celery argument, so we can't
    release the lock in an async chain.
    """

    def __init__(self, conn, name, unique_id=None):
        self.conn = conn
        self.name = name
        if unique_id is None:
            self.unique_id = str(uuid.uuid4())
        else:
            self.unique_id = unique_id

    def acquire(self, acquire_timeout=10, lock_expiry=None):
        end = time.time() + acquire_timeout
        while time.time() < end:
            if self.conn.set(self.name, self.unique_id, ex=lock_expiry, nx=True):
                LOG.debug("Acquired lock: %s(%s)", self.name, self.unique_id)
                return self.unique_id

            time.sleep(0.05)

        LOG.debug("Failed to acquire lock: %s(%s)", self.name, self.unique_id)
        return None

    def release(self):
        with self.conn.pipeline() as pipe:
            while True:
                try:
                    pipe.watch(self.name)
                    existing = pipe.get(self.name)
                    if not isinstance(existing, str):
                        existing = existing.decode("ascii")

                    if existing == self.unique_id:
                        pipe.multi()
                        pipe.delete(self.name)
                        pipe.execute()
                        LOG.debug("Released lock: %s(%s)", self.name, self.unique_id)
                        return True

                    pipe.unwatch()
                    break

                except redis.exceptions.WatchError:
                    pass

        LOG.debug(
            "Failed to release lock: %s(%s) != %s", self.name, self.unique_id, existing
        )
        return False

def get_client_ip(request):
    """
    Extracts the client IP address from request headers.
    """
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")
    
    return ip

class IPRestrictedTokenAuthentication(TokenAuthentication):
    def authenticate(self, request):
        if  self.is_ip_restricted(request):
            raise PermissionDenied("IP address restricted. Access denied.")

        return super().authenticate(request)

    def is_ip_restricted(self, request):
        allowed_ips = set(getattr(settings, "ALLOWED_IPS", []))
        client_ip = get_client_ip(request)
        if client_ip not in allowed_ips:
            LOG.warning(f"IP address restricted: {client_ip}")
            return True

        return False
