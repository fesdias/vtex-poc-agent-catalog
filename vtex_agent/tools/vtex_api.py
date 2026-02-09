"""Low-level VTEX API layer. Used internally by vtex_catalog_tools."""
import os
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

load_dotenv()

_api_instance = None


def _get_api():
    """Return the singleton API instance (lazy init)."""
    global _api_instance
    if _api_instance is None:
        _api_instance = _VTEXAPI()
    return _api_instance


class _VTEXAPI:
    """Internal API layer for VTEX HTTP requests."""

    def __init__(
        self,
        account_name: Optional[str] = None,
        environment: str = "vtexcommercestable",
        app_key: Optional[str] = None,
        app_token: Optional[str] = None,
    ):
        self.account_name = account_name or os.getenv("VTEX_ACCOUNT_NAME")
        self.environment = environment
        self.app_key = app_key or os.getenv("VTEX_APP_KEY")
        self.app_token = app_token or os.getenv("VTEX_APP_TOKEN")

        if not all([self.account_name, self.app_key, self.app_token]):
            raise ValueError(
                "VTEX credentials required. Set VTEX_ACCOUNT_NAME, "
                "VTEX_APP_KEY, and VTEX_APP_TOKEN in .env"
            )

        self.base_url = f"https://{self.account_name}.{self.environment}.com.br"
        self.headers = {
            "X-VTEX-API-AppKey": self.app_key,
            "X-VTEX-API-AppToken": self.app_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def catalog_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        """Make a request to the Catalog API."""
        url = f"{self.base_url}/api/catalog/{endpoint}"
        return self._request(method, url, data, params)

    def _request(
        self,
        method: str,
        url: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> requests.Response:
        """Make HTTP request with error handling."""
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                params=params,
                headers=self.headers,
                timeout=30,
            )

            if not response.ok:
                error_msg = response.text[:300] if response.text else "No error message"
                print(f"   ⚠️  VTEX API Error [{response.status_code}] {method} {url}")
                print(f"       Response: {error_msg}")
                if response.status_code == 404:
                    print(f"       Full URL: {url}")

            return response
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Request exception: {e}")
            class MockResponse:
                status_code = 500
                text = str(e)
                def json(self):
                    return {}
                def raise_for_status(self):
                    pass
            return MockResponse()
