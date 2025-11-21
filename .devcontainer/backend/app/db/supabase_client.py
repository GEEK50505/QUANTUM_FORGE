"""
Supabase REST API Client for Quantum Forge

Uses Supabase's auto-generated REST API (PostgREST) instead of direct PostgreSQL.
This works through HTTP/HTTPS, avoiding firewall issues with port 5432.

Features:
- No direct database connection required
- Works through HTTP/443
- Full CRUD operations via REST endpoints
- Automatic JSON serialization
- Real-time subscription support (future)

The Supabase REST API provides automatic endpoints for all tables:
- GET /rest/v1/{table}
- POST /rest/v1/{table}
- PATCH /rest/v1/{table}
- DELETE /rest/v1/{table}
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode

import requests
from functools import lru_cache
import time

logger = logging.getLogger(__name__)


class SupabaseSchemaError(Exception):
    """Base exception for Supabase schema-related errors."""
    pass


class SupabaseColumnNotFound(SupabaseSchemaError):
    """Raised when PostgREST reports a missing column in the schema cache."""
    def __init__(self, column: str, message: str = ''):
        super().__init__(message or f"Supabase column not found: {column}")
        self.column = column



class SupabaseClient:
    """
    Supabase REST API client for database operations.
    
    Communicates with PostgreSQL through Supabase's PostgREST API.
    All operations use HTTP, making it firewall-friendly.
    """
    
    def __init__(self, url: str, api_key: str):
        """
        Initialize Supabase client.
        
        Args:
            url: Supabase project URL (https://project.supabase.co)
            api_key: Supabase anon or service_role API key
        """
        self.url = url.rstrip('/')
        self.api_key = api_key
        self.base_url = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",  # Return inserted/updated rows
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        # Cache for table writable columns discovered via OPTIONS
        self._table_columns_cache: Dict[str, Dict[str, List[str]]] = {}
    
    def health_check(self) -> bool:
        """
        Check if Supabase connection is healthy.
        
        Returns:
            True if connected, False otherwise
        """
        try:
            # Simple health check: query molecules table (exists after schema.sql)
            url = f"{self.base_url}/molecules?limit=1&select=id"
            response = self.session.get(url, timeout=10)
            return response.status_code in [200, 206]
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _get_table_writable_columns(self, table: str, method: str = 'insert') -> List[str]:
        """
        Discover writable columns for a table using HTTP OPTIONS on the PostgREST endpoint.

        PostgREST returns headers such as 'Accept-Post' and 'Accept-Patch' which list
        allowed columns. We cache results per-instance to avoid repeated OPTIONS calls.
        """
        try:
            cache_key = f"{table}:{method}"
            if cache_key in self._table_columns_cache:
                return self._table_columns_cache[cache_key]

            url = f"{self.base_url}/{table}"
            resp = self.session.options(url, timeout=5)
            header = None
            if method == 'insert':
                header = resp.headers.get('Accept-Post')
            else:
                header = resp.headers.get('Accept-Patch')

            cols: List[str] = []
            if header:
                cols = [c.strip() for c in header.split(',') if c.strip()]

            # Cache results (even empty list to avoid repeated network calls)
            self._table_columns_cache[cache_key] = cols
            return cols
        except Exception:
            return []
    
    def get(
        self,
        table: str,
        filters: Optional[Dict[str, Any]] = None,
        select: str = "*",
        limit: Optional[int] = None,
        offset: int = 0,
        order_by: Optional[str] = None,
    ) -> List[Dict]:
        """
        Fetch rows from a table.
        
        Args:
            table: Table name
            filters: Column=value filters (e.g., {"user_id": "123", "status": "completed"})
            select: Columns to return (e.g., "id,name,energy")
            limit: Maximum rows to return
            offset: Number of rows to skip
            order_by: Column and direction (e.g., "created_at.desc")
        
        Returns:
            List of rows as dictionaries
        
        Example:
            >>> client.get("molecules", select="id,name,smiles")
            >>> client.get("calculations", filters={"gap": (0.0, 5.0)}, order_by="gap.asc")
        """
        try:
            params = {"select": select}
            
            # Add filters
            if filters:
                for key, value in filters.items():
                    if isinstance(value, (list, tuple)) and len(value) == 2:
                        # Range query: {"gap": (0.0, 5.0)} → "gap=gte.0.0&gap=lte.5.0"
                        params[f"{key}"] = f"gte.{value[0]}"
                        params[f"{key}"] = f"lte.{value[1]}"
                    elif value is None:
                        params[key] = "is.null"
                    else:
                        params[key] = f"eq.{value}"
            
            if limit:
                params["limit"] = limit
            if offset:
                params["offset"] = offset
            if order_by:
                params["order"] = order_by
            
            url = f"{self.base_url}/{table}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"GET {table} failed: {e}")
            return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[Dict]:
        """
        Insert a single row.
        
        Args:
            table: Table name
            data: Column values as dict
        
        Returns:
            Inserted row with generated ID
        
        Example:
            >>> mol = client.insert("molecules", {
            ...     "name": "water",
            ...     "smiles": "O",
            ...     "formula": "H2O",
            ...     "user_id": "user-123"
            ... })
        """
        try:
            url = f"{self.base_url}/{table}"
            # Retry transient failures with exponential backoff
            max_attempts = 3
            backoff_base = 1.5
            attempt = 0
            last_exception = None
            try:
                payload_snippet = json.dumps(data, default=str)[:1000]
            except Exception:
                payload_snippet = str(data)[:1000]
            logger.debug(f"INSERT {table} payload: {payload_snippet}")
            # Pre-sanitize payload using PostgREST OPTIONS response when available
            try:
                allowed = self._get_table_writable_columns(table, method='insert')
                if allowed and isinstance(data, dict):
                    removed = [k for k in data.keys() if k not in allowed]
                    if removed:
                        # Log at warning so operators can act on missing server-side columns
                        logger.warning(
                            f"Sanitizing INSERT payload for {table}: removing keys not in schema: {removed}. "
                            f"If these fields are required, add them to the Supabase table schema."
                        )
                    sanitized_data = {k: v for k, v in data.items() if k in allowed}
                else:
                    sanitized_data = dict(data) if isinstance(data, dict) else data
            except Exception:
                sanitized_data = dict(data) if isinstance(data, dict) else data

            # Support iterative sanitized retries when PostgREST reports missing columns
            sanitized_attempts = 0
            max_sanitized_attempts = 6

            while attempt < max_attempts:
                attempt += 1
                try:
                    response = self.session.post(url, json=sanitized_data, timeout=10)

                    # If 400-level client error, attempt to detect schema issues
                    if 400 <= response.status_code < 500:
                        # Try to parse PostgREST error message to detect missing column/table
                        msg = None
                        try:
                            body = response.json() if response is not None else {}
                            msg = body.get('message') if isinstance(body, dict) else None
                        except Exception:
                            msg = response.text if response is not None else None

                        if isinstance(msg, str) and "Could not find the '" in msg:
                            try:
                                parts = msg.split("'")
                                reported = parts[1] if len(parts) >= 2 else None
                                # If it's a column message, try removing that top-level key and retry
                                if reported and 'column' in msg and isinstance(sanitized_data, dict):
                                    if reported in sanitized_data and sanitized_attempts < max_sanitized_attempts:
                                        sanitized_attempts += 1
                                        logger.warning(f"Supabase schema mismatch: missing column '{reported}' when inserting into {table}; removing key and retrying (attempt {sanitized_attempts})")
                                        # Remove the offending top-level key and retry using the same outer loop
                                        sanitized_data = {k: v for k, v in sanitized_data.items() if k != reported}
                                        # Reset last_exception for next try
                                        last_exception = None
                                        # Continue to next attempt without sleeping (sanitization is immediate)
                                        continue
                                    else:
                                        # Column not present in payload or we've exhausted sanitize attempts
                                        logger.error(f"Supabase reported missing column '{reported}' but it is not present in payload or sanitize limit reached")
                                        return None
                                # If the message mentions 'table', surface a helpful log and return None
                                if reported and 'table' in msg:
                                    logger.error(f"Supabase table not found when inserting into {table}: {msg}")
                                    return None
                            except Exception:
                                logger.error(f"INSERT {table} failed with status={response.status_code}: {response.text}")
                                return None
                        else:
                            logger.error(f"INSERT {table} failed with status={response.status_code}: {response.text}")
                            return None

                    response.raise_for_status()
                    result = response.json()
                    return result[0] if isinstance(result, list) else result
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    # If it's a server error or timeout, retry after backoff
                    status = None
                    try:
                        status = getattr(e.response, 'status_code', None)
                    except Exception:
                        status = None

                    # For 5xx or network errors retry, else break
                    if status is None or (500 <= status < 600) or isinstance(e, requests.exceptions.Timeout):
                        sleep_time = backoff_base ** attempt
                        logger.warning(f"Transient error inserting into {table} (attempt {attempt}/{max_attempts}): {e}; retrying in {sleep_time:.1f}s")
                        time.sleep(sleep_time)
                        continue
                    else:
                        logger.error(f"INSERT {table} failed (non-retryable): {e}")
                        # Attempt to surface PostgREST schema errors to callers
                        try:
                            # Parse JSON body for schema errors like PGRST204
                            body = response.json() if response is not None else {}
                            msg = body.get('message') if isinstance(body, dict) else None
                            if msg and isinstance(msg, str) and "Could not find the '" in msg:
                                # Extract column name between single quotes
                                start = msg.find("Could not find the '")
                                if start != -1:
                                    # Format: Could not find the 'column' column of 'table' in the schema cache
                                    try:
                                        col = msg.split("'")[1]
                                        raise SupabaseColumnNotFound(col, msg)
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                        return None

            # If we reach here, all attempts failed
            logger.error(f"INSERT {table} failed after {max_attempts} attempts: {last_exception}")
            return None
        
        except requests.exceptions.RequestException as e:
            # If response is attached to the exception, try to log it
            try:
                resp = e.response
                if resp is not None:
                    logger.error(f"INSERT {table} failed: status={resp.status_code} body={resp.text}")
                else:
                    logger.error(f"INSERT {table} failed: {e}")
            except Exception:
                logger.error(f"INSERT {table} failed: {e}")
            return None
    
    def insert_many(self, table: str, rows: List[Dict[str, Any]]) -> List[Dict]:
        """
        Bulk insert multiple rows.
        
        Args:
            table: Table name
            rows: List of row dicts
        
        Returns:
            List of inserted rows with generated IDs
        
        Example:
            >>> molecules = [
            ...     {"name": "water", "smiles": "O", "formula": "H2O"},
            ...     {"name": "methane", "smiles": "C", "formula": "CH4"},
            ... ]
            >>> client.insert_many("molecules", molecules)
        """
        try:
            url = f"{self.base_url}/{table}"
            # Pre-sanitize rows if we can discover writable columns
            try:
                allowed = self._get_table_writable_columns(table, method='insert')
                if allowed:
                    # Warn about keys removed for bulk inserts too
                    sanitized_rows = []
                    for r in rows:
                        removed = [k for k in r.keys() if k not in allowed]
                        if removed:
                            logger.warning(f"Sanitizing INSERT MANY payload for {table}: removing keys not in schema: {removed}")
                        sanitized_rows.append({k: v for k, v in r.items() if k in allowed})
                else:
                    sanitized_rows = rows
            except Exception:
                sanitized_rows = rows

            response = self.session.post(url, json=sanitized_rows, timeout=30)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"INSERT MANY {table} failed: {e}")
            return []
    
    def update(
        self,
        table: str,
        data: Dict[str, Any],
        filters: Dict[str, Any],
    ) -> List[Dict]:
        """
        Update rows matching filters.
        
        Args:
            table: Table name
            data: Columns to update
            filters: WHERE clause (e.g., {"id": 123})
        
        Returns:
            Updated rows
        
        Example:
            >>> client.update("batch_jobs",
            ...     data={"status": "completed", "completed_at": "2025-11-14T12:00:00Z"},
            ...     filters={"id": 42}
            ... )
        """
        try:
            params = {}
            for key, value in filters.items():
                if value is None:
                    params[key] = "is.null"
                else:
                    params[key] = f"eq.{value}"
            
            url = f"{self.base_url}/{table}"
            # Sanitize update payload to allowed patch columns if discoverable
            try:
                allowed = self._get_table_writable_columns(table, method='patch')
                if allowed:
                    removed = [k for k in data.keys() if k not in allowed]
                    if removed:
                        logger.warning(f"Sanitizing UPDATE payload for {table}: removing keys not in schema: {removed}")
                    sanitized = {k: v for k, v in data.items() if k in allowed}
                else:
                    sanitized = data
            except Exception:
                sanitized = data

            response = self.session.patch(url, json=sanitized, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"UPDATE {table} failed: {e}")
            return []
    
    def delete(self, table: str, filters: Dict[str, Any]) -> int:
        """
        Delete rows matching filters.
        
        Args:
            table: Table name
            filters: WHERE clause
        
        Returns:
            Number of deleted rows
        
        Example:
            >>> client.delete("batch_items", {"batch_id": 42})
        """
        try:
            params = {}
            for key, value in filters.items():
                if value is None:
                    params[key] = "is.null"
                else:
                    params[key] = f"eq.{value}"
            
            url = f"{self.base_url}/{table}"
            response = self.session.delete(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Extract count from response headers
            count = response.headers.get("X-Total-Delete-Count", 0)
            return int(count)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"DELETE {table} failed: {e}")
            return 0
    
    def rpc(self, function: str, params: Dict[str, Any] = None) -> Any:
        """
        Call a stored procedure / RPC function.
        
        Args:
            function: Function name
            params: Function parameters
        
        Returns:
            Function result
        
        Example:
            >>> result = client.rpc("get_molecule_statistics", {"user_id": "123"})
        """
        try:
            url = f"{self.url}/rest/v1/rpc/{function}"
            response = self.session.post(url, json=params or {}, timeout=10)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"RPC {function} failed: {e}")
            return None


@lru_cache(maxsize=1)
def get_supabase_client() -> SupabaseClient:
    """
    Get or create Supabase client singleton.
    
    Reads credentials from environment variables:
    - SUPABASE_URL: https://project.supabase.co
    - SUPABASE_KEY: Anon or service_role API key
    
    Returns:
        SupabaseClient instance
    
    Raises:
        ValueError: If credentials not configured
    """
    supabase_url = os.getenv("SUPABASE_URL")
    # Prefer an explicit service role / admin key if provided for server-side writes
    supabase_service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY")
    supabase_key = supabase_service_key or os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY)"
        )

    if supabase_service_key:
        logger.info("Using SUPABASE_SERVICE_ROLE_KEY for Supabase client (server-side writes permitted).")
    else:
        logger.warning("No SUPABASE_SERVICE_ROLE_KEY detected. Using SUPABASE_KEY — ensure RLS policies allow writes or set a service role key for migrations and server writes.")

    logger.info(f"Initializing Supabase client for {supabase_url}")
    return SupabaseClient(supabase_url, supabase_key)
