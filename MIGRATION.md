Awesome — here’s a complete **`MIGRATION.md`** you can drop into the repo to help users move from schema v1 → **schema v2 (`ssutxos-2`)**.

````markdown
# Migration Guide: v1 → v2 (`ssutxos-2`)

This guide explains how to migrate existing **ssutxos** snapshot files produced by older versions
(v1-style JSON) into the new **schema v2** format. The v2 schema supports **spent** and **unspent**
UTXOs and is used by the `compare` command.

---

## 1) What changed in v2?

### Top-level
| v1 (old)     | v2 (new)          | Notes                                                   |
|--------------|-------------------|---------------------------------------------------------|
| *(none)*     | `schema`          | Must be `"ssutxos-2"`.                                 |
| `network`    | `network`         | Same semantics (`liquidv1` or `testnet`).              |
| *(none)*     | `generated_at`    | ISO-8601 UTC timestamp of snapshot creation.           |
| *(none?)*    | `wallet`          | Info about the source (e.g. `"mnemonic"` / descriptor).|
| `utxos`      | `utxos`           | Array of UTXO objects; structure updated (below).      |

### Per-UTXO
| v1 (old)           | v2 (new)                | Notes                                                                 |
|--------------------|-------------------------|-----------------------------------------------------------------------|
| `txid`             | `txid`                  | Same.                                                                 |
| `vout`             | `vout`                  | Same.                                                                 |
| *(none)*           | `id`                    | **New**: formatted as `"txid:vout"` for fast lookups.                 |
| *(unspent only)*   | `status`                | **New**: `"unspent"` or `"spent"`.                                    |
| `address`          | `address`               | Optional; keep if available.                                          |
| `script_pubkey`    | `script_pubkey`         | Optional; keep if available.                                          |
| `asset` / `asset_id` | `asset`               | Prefer `asset` in v2.                                                 |
| `amount_sat`/`value`| `amount_sat`           | Store satoshis as integer.                                            |
| `block_height`     | `block_height`          | Optional.                                                             |
| `block_time`       | `block_time`            | Optional (unix epoch seconds).                                        |
| *(none)*           | `spending_txid`         | **New**: If known (for spent outputs).                                |
| *(none)*           | `spending_block_time`   | **New**: If known (unix epoch seconds).                               |
| *(none)*           | `metadata`              | **New**: Arbitrary extensible object.                                 |

> If your v1 files have only **unspent** outputs, they will be migrated with `status="unspent"` and `spending_* = null`.

---

## 2) Minimal transformation rules

1. Add top-level:
   ```json
   "schema": "ssutxos-2",
   "generated_at": "<UTC ISO timestamp>",
   "wallet": {"source": "migration"}
````

2. For each UTXO, add:

   ```json
   "id": "<txid>:<vout>",
   "status": "unspent",
   "metadata": {}
   ```
3. Normalize fields:

   * Prefer `asset` over `asset_id`.
   * Prefer `amount_sat` (convert from `value` if needed).
4. Leave unknowns as `null`:

   * `block_height`, `block_time`, `spending_txid`, `spending_block_time`.

> To enrich **spent** info post-migration, you can query Esplora `/tx/<txid>/outspend/<vout>` and fill `status="spent"` plus `spending_txid` / `spending_block_time` if reported.

---

## 3) One-liner `jq` example (quick & dirty)

> Assumes input is `v1.json` with a top-level `network` and `utxos[]` containing `txid`/`vout`/`amount_sat|value`.

```bash
jq '
  . as $root |
  {
    schema: "ssutxos-2",
    network: ($root.network // "liquidv1"),
    generated_at: (now | todateiso8601),
    wallet: { source: "migration" },
    utxos: ($root.utxos // []) | map(
      .asset as $a
      | .asset_id as $aid
      | .value as $val
      | .amount_sat as $amt
      | {
          id: ([.txid, (.vout|tostring)] | join(":")),
          status: "unspent",
          txid: .txid,
          vout: .vout,
          address: (.address // null),
          script_pubkey: (.script_pubkey // .script // null),
          asset: ($a // $aid // "LBTC"),
          amount_sat: (($amt // $val // 0)|tonumber),
          block_height: (.block_height // .height // null),
          block_time: (.block_time // .time // null),
          first_seen: null,
          last_seen: null,
          spending_txid: null,
          spending_block_time: null,
          metadata: {}
        }
    )
  }
' v1.json > v2.json
```

---

## 4) Python migration script (v1 → v2)

Save as `scripts/migrate_v1_to_v2.py`:

```python
#!/usr/bin/env python3
import json, sys, time
from datetime import datetime, timezone
from pathlib import Path

def to_int(v):
    try:
        return int(v)
    except Exception:
        return None

def main(inp: str, out: str):
    data = json.loads(Path(inp).read_text())
    utxos = data.get("utxos", [])

    v2 = {
        "schema": "ssutxos-2",
        "network": data.get("network", "liquidv1"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "wallet": {"source": "migration"},
        "utxos": []
    }

    for u in utxos:
        txid = u.get("txid")
        vout = u.get("vout")
        if txid is None or vout is None:
            continue

        amount_sat = (
            u.get("amount_sat", u.get("value", 0))
        )
        amount_sat = int(amount_sat) if amount_sat is not None else 0

        asset = u.get("asset", u.get("asset_id", "LBTC"))
        script_pubkey = u.get("script_pubkey", u.get("script"))

        v2["utxos"].append({
            "id": f"{txid}:{int(vout)}",
            "status": "unspent",
            "txid": txid,
            "vout": int(vout),
            "address": u.get("address"),
            "script_pubkey": script_pubkey,
            "asset": asset,
            "amount_sat": amount_sat,
            "block_height": u.get("block_height", u.get("height")),
            "block_time": u.get("block_time", u.get("time")),
            "first_seen": None,
            "last_seen": None,
            "spending_txid": None,
            "spending_block_time": None,
            "metadata": {}
        })

    Path(out).write_text(json.dumps(v2, indent=2))
    print(f"Wrote {out} with {len(v2['utxos'])} UTXOs (schema=ssutxos-2)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: migrate_v1_to_v2.py <v1.json> <v2.json>", file=sys.stderr)
        sys.exit(2)
    main(sys.argv[1], sys.argv[2])
```

Run:

```bash
python scripts/migrate_v1_to_v2.py old_v1.json new_v2.json
```

---

## 5) (Optional) Enrich “spent” info after migration

If your v1 file never tracked spends, you can augment the v2 file by querying Esplora for outspends:

```bash
# For each utxo in v2.json (pseudo-commands):
# GET /tx/<txid>/outspend/<vout> -> {"spent": true|false, "txid": "...", ...}
# If spent: set status="spent", spending_txid, and try /tx/<spending_txid> to read a block_time.

# Example curl:
curl -s "https://blockstream.info/liquid/api/tx/<TXID>/outspend/<VOUT>"
```

You can also just use `ssutxos list` (LWK + Esplora) to regenerate a fresh snapshot that already includes spent state.

---

## 6) Validating migrated files

* Check the **schema id**:

  ```bash
  jq -r '.schema' v2.json
  # => ssutxos-2
  ```
* Sanity check IDs:

  ```bash
  jq -r '.utxos[].id' v2.json | head
  # => <txid>:<vout>
  ```
* Dry-run `compare` with two v2 snapshots:

  ```bash
  ssutxos compare a_v2.json b_v2.json --esplora https://blockstream.info/liquid/api --delay-ms 200
  ```

---

## 7) FAQs

**Q: Can I still use v1 files with `compare`?**
A: `compare` expects `id` fields and may assume v2 layout. Migrate to v2 first.

**Q: I only have unspent outputs in v1. Is that OK?**
A: Yes. Migrate and everything will be marked `status="unspent"`. You can enrich spends later.

**Q: Do I need LWK to migrate?**
A: No. Migration is a JSON-level transform; LWK is only needed to *generate* new snapshots with wallet discovery.

---

**Happy tracing!**

```

If you want, I can also drop this file straight into your repo (beside `README.md` and `CHANGELOG.md`) and commit message text you can reuse.
```
