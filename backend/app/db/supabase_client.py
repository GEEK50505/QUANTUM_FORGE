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

logger = logging.getLogger(__name__)


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
            response = self.session.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return result[0] if isinstance(result, list) else result
        
        except requests.exceptions.RequestException as e:
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
            response = self.session.post(url, json=rows, timeout=30)
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
            response = self.session.patch(url, json=data, params=params, timeout=10)
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
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        raise ValueError(
            "Supabase credentials not configured. Set SUPABASE_URL and SUPABASE_KEY"
        )
    
    logger.info(f"Initializing Supabase client for {supabase_url}")
    return SupabaseClient(supabase_url, supabase_key)
