import threading
import time
import os
from typing import Optional, Callable

try:
    from supabase import create_client
except Exception:
    create_client = None


class LogSyncer:
    """Background thread that tails a file and periodically uploads it to Supabase Storage.

    Usage:
      syncer = LogSyncer(local_path, supabase_url, supabase_key, 'job_artifacts', remote_path)
      syncer.start()
      ... write to local_path from process stdout ...
      syncer.stop_and_finish()
    """

    def __init__(self, local_path: str, supabase_url: Optional[str], supabase_key: Optional[str],
                 bucket: str, remote_path: str, interval_seconds: float = 3.0):
        self.local_path = local_path
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.bucket = bucket
        self.remote_path = remote_path
        self.interval_seconds = interval_seconds

        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._client = None

    def start(self):
        if self.supabase_url and self.supabase_key and create_client:
            try:
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception:
                self._client = None
        self._thread.start()

    def stop_and_finish(self):
        self._stop.set()
        self._thread.join(timeout=10)
        # One final upload
        self._upload_if_possible()

    def _run(self):
        while not self._stop.is_set():
            self._upload_if_possible()
            # sleep in small increments so stop can be responsive
            for _ in range(int(self.interval_seconds * 10)):
                if self._stop.is_set():
                    break
                time.sleep(0.1)

    def _upload_if_possible(self):
        if not (self.supabase_url and self.supabase_key and create_client and os.path.exists(self.local_path)):
            return
        try:
            # Use a fresh client if we couldn't create one earlier
            client = self._client or create_client(self.supabase_url, self.supabase_key)
            with open(self.local_path, 'rb') as f:
                data = f.read()
            if not data:
                # avoid empty uploads
                return
            # upload/overwrite the file
            client.storage.from_(self.bucket).upload(self.remote_path, data)
            # ensure content-type is text/plain when possible (some client versions accept options)
        except Exception:
            # best-effort: don't propagate uploader errors to main job
            return
