from dataclasses import dataclass
from typing import List, Set, Iterable, Callable, Any
from .explorer import EsploraClient


@dataclass(frozen=True)
class Outpoint:
    """Represents a transaction outpoint (txid + vout index)."""
    txid: str
    vout: int


def parse_outpoints(data: Any) -> List[Outpoint]:
    """
    Parse UTXOs from JSON into a list of Outpoint objects.
    Supports:
      - {"utxos": [ ... ]}
      - [ ... ] (plain list of utxo dicts)
    """
    if isinstance(data, dict) and "utxos" in data:
        items = data["utxos"] or []
    elif isinstance(data, list):
        items = data
    else:
        return []

    outpoints: List[Outpoint] = []
    for u in items:
        txid = u.get("txid")
        vout = u.get("vout")
        if txid is None or vout is None:
            continue
        outpoints.append(Outpoint(str(txid), int(vout)))
    return outpoints


def bfs_descendants(
    start: Iterable[Outpoint],
    is_target: Callable[[Outpoint], bool],
    api: EsploraClient,
    on_found: Callable[[Outpoint, int], None],
    on_round_begin: Callable[[int], None],
    on_round_end: Callable[[int, int, int], None],
) -> None:
    """
    Breadth-first search expanding through spends.

    - start: initial outpoints
    - is_target: returns True if outpoint matches target set
    - api: EsploraClient instance
    - on_found: called when a target outpoint is found
    - on_round_begin: called at start of each hop
    - on_round_end: called at end of each hop with (hop, processed, new_in_round)

    Runs indefinitely until KeyboardInterrupt is raised by caller.
    """
    visited: Set[Outpoint] = set()
    frontier: List[Outpoint] = list(start)
    hop = 0

    while True:
        on_round_begin(hop)
        processed = 0
        new_count = 0

        # consume current frontier
        this_round, frontier = frontier, []
        for op in this_round:
            if op in visited:
                continue
            visited.add(op)
            processed += 1

            # check target
            if is_target(op):
                on_found(op, hop)

            # expand descendants
            outsp = api.get_outspend(op.txid, op.vout)
            if outsp and outsp.get("spent"):
                spender_txid = outsp.get("txid")
                if spender_txid:
                    tx = api.get_tx(spender_txid)
                    for idx in range(len(tx.get("vout", []))):
                        child = Outpoint(spender_txid, idx)
                        if child not in visited:
                            frontier.append(child)
                            new_count += 1

        on_round_end(hop, processed, new_count)
        hop += 1