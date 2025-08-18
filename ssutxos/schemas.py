
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime, timezone

SCHEMA_ID = "ssutxos-2"

@dataclass
class UTXO:
    id: str                # "<txid>:<vout>"
    status: Literal["unspent", "spent"]
    txid: str
    vout: int
    address: Optional[str]
    script_pubkey: Optional[str]
    asset: Optional[str]
    amount_sat: int
    block_height: Optional[int] = None
    block_time: Optional[int] = None
    first_seen: Optional[int] = None
    last_seen: Optional[int] = None
    spending_txid: Optional[str] = None
    spending_block_time: Optional[int] = None
    # extensible
    metadata: Dict[str, Any] = None

@dataclass
class Snapshot:
    schema: str
    network: Literal["liquidv1", "testnet"]  # esplora: liquid.network vs liquid.testnet
    generated_at: str
    wallet: Dict[str, Any]
    utxos: List[UTXO]

    @staticmethod
    def new(network: str, wallet: Dict[str, Any], utxos: List[UTXO]) -> "Snapshot":
        return Snapshot(
            schema=SCHEMA_ID,
            network=network,
            generated_at=datetime.now(tz=timezone.utc).isoformat(),
            wallet=wallet,
            utxos=utxos,
        )

    def to_json(self) -> Dict[str, Any]:
        d = asdict(self)
        # ensure ints are ints
        return d
