import requests
import time
from typing import Optional, Dict, Any


class EsploraClient:
    """
    Minimal Esplora API client for Liquid.

    Supports:
      - get_outspend(txid, vout)
      - get_tx(txid)
    """

    def __init__(self, base_url: str = "https://blockstream.info/liquid/api", sleep_ms: int = 100):
        self.base_url = base_url.rstrip("/")
        self.sleep_ms = sleep_ms / 1000.0  # convert ms to seconds

    def _sleep(self) -> None:
        """Sleep between API calls to avoid rate limits."""
        if self.sleep_ms > 0:
            time.sleep(self.sleep_ms)

    def _get(self, path: str) -> Optional[Dict[str, Any]]:
        """Internal GET helper with error handling."""
        url = f"{self.base_url}{path}"
        try:
            resp = requests.get(url, timeout=30)
            self._sleep()
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"Warning: GET {url} -> {resp.status_code}")
                return None
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_outspend(self, txid: str, vout: int) -> Optional[Dict[str, Any]]:
        """
        Get spend status of a transaction output.

        Example return:
        {
          "spent": true,
          "txid": "....",
          "vin": 0,
          ...
        }
        """
        return self._get(f"/tx/{txid}/outspend/{vout}")

    def get_tx(self, txid: str) -> Optional[Dict[str, Any]]:
        """
        Get transaction details.

        Example return contains "vin" and "vout".
        """
        return self._get(f"/tx/{txid}")
