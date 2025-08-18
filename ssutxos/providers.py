
from __future__ import annotations
import time
import requests
from typing import Dict, Any, List, Optional, Tuple, Iterable

class RateLimiter:
    def __init__(self, min_ms: int = 100):
        self.min_ms = max(0, min_ms)
        self._last = 0.0

    def wait(self):
        now = time.time()
        delta = (self._last + self.min_ms/1000.0) - now
        if delta > 0:
            time.sleep(delta)
        self._last = time.time()

class EsploraProvider:
    def __init__(self, base_url: str, rate_ms: int = 100):
        self.base = base_url.rstrip("/")
        self.rl = RateLimiter(rate_ms)

    def _get(self, path: str) -> Any:
        self.rl.wait()
        url = f"{self.base}{path}"
        r = requests.get(url, timeout=30)
        r.raise_for_status()
        return r.json()

    def tx(self, txid: str) -> Dict[str, Any]:
        return self._get(f"/tx/{txid}")

    def tx_outspend(self, txid: str, vout: int) -> Dict[str, Any]:
        return self._get(f"/tx/{txid}/outspend/{vout}")

    def address_utxo(self, address: str) -> List[Dict[str, Any]]:
        return self._get(f"/address/{address}/utxo")

def neighbors_from_tx(tx: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Return (prevouts, outputs) as utxo ids '<txid>:<vout>' for graph traversal."""
    prevs = []
    for vin in tx.get("vin", []):
        prevs.append(f"{vin['txid']}:{vin['vout']}")
    outs = []
    for i, vout in enumerate(tx.get("vout", [])):
        outs.append(f"{tx['txid']}:{i}")
    return prevs, outs
