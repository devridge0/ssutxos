
from __future__ import annotations
import json
import signal
from collections import deque
from typing import Dict, Set, List, Tuple, Iterable, Optional

from .providers import EsploraProvider, neighbors_from_tx

class StopRequested(Exception):
    pass

def sigint_handler(signum, frame):
    raise StopRequested()

def load_ids(snapshot: Dict) -> Set[str]:
    utxos = snapshot.get("utxos", [])
    ids = set()
    for u in utxos:
        uid = u.get("id") or f"{u.get('txid')}:{u.get('vout')}"
        if uid and ':' in uid:
            ids.add(uid)
    return ids

def compare_loop(
    utxos1: Dict,
    utxos2: Dict,
    esplora_base: str,
    delay_ms: int = 100,
):
    signal.signal(signal.SIGINT, sigint_handler)
    provider = EsploraProvider(esplora_base, delay_ms)

    target_ids = load_ids(utxos1)
    frontier: deque[str] = deque(load_ids(utxos2))
    seen: Set[str] = set(frontier)

    hop = 0
    print("Starting from utxos1.json utxos.")
    while True:
        print(f"Searching in utxos2.json-derived utxos {hop} hops out...")
        new_count = 0
        found_any = False
        # BFS sweep for this hop
        next_frontier: deque[str] = deque()
        while frontier:
            uid = frontier.popleft()
            txid, vout_s = uid.split(":")
            vout = int(vout_s)
            try:
                tx = provider.tx(txid)
            except Exception as e:
                print(f"  error fetching tx {txid}: {e}")
                continue

            prevs, outs = neighbors_from_tx(tx)

            # include outspend to follow spends
            try:
                outspend = provider.tx_outspend(txid, vout)
                if outspend and outspend.get("spent"):
                    spend_txid = outspend.get("txid")
                    if spend_txid:
                        try:
                            stx = provider.tx(spend_txid)
                            s_prevs, s_outs = neighbors_from_tx(stx)
                            outs.extend(s_outs)
                        except Exception as e:
                            pass
            except Exception:
                pass

            # Consider neighbors as prevs + outs
            for nid in prevs + outs:
                if nid in seen:
                    continue
                seen.add(nid)
                next_frontier.append(nid)
                new_count += 1
                if nid in target_ids:
                    print(f"  FOUND a utxo: {nid}")
                    found_any = True
        print(f"  new utxos encountered in this round: {new_count}")
        if not found_any:
            print("  nothing found")
        frontier = next_frontier
        hop += 1
