
# A CLI tool to inspect SideSwap UTXOs

`ssutxos` is a Python command-line interface (CLI) tool for inspecting and tracing **Liquid Network UTXOs** (both unspent and spent).  
It is designed for research, wallet analysis, and graph exploration across snapshots of wallet states.

---

## Features

- **List** UTXOs (spent + unspent) for a wallet derived from a **BIP39 mnemonic** using **LWK** (Liquid Wallet Kit).  
  - If LWK does not expose spent state, `ssutxos` consults **Esplora** to determine whether outputs are spent.  
  - Produces a standardized **schema v2 JSON snapshot** (`ssutxos-2`).
- **Compare** two snapshot files by traversing the **transaction graph outward indefinitely**, hop by hop, until interrupted.  
  - Reports when UTXOs from one snapshot are connected to UTXOs in the other.  
  - Uses **Esplora API** for fetching transactions and spends.  
  - Supports configurable API throttling (`--delay-ms`) to respect rate limits.
- Built with **Typer** for a clean, modern CLI.

---

## Installation

Clone the repo and install locally:

```bash
git clone https://github.com/devridge0/ssutxos.git
cd ssutxos
python -m venv lwk-venv
source lwk-venv/bin/activate
pip install -r requirements.txt
pip install .
````

Or install from the built wheel:

```bash
pip install dist/ssutxos-0.1.0-py3-none-any.whl
```

---

## Usage

### Show Version

```bash
ssutxos --version
```

### List UTXOs

```bash
ssutxos list --mnemonic "your twelve or twenty-four word mnemonic" \
             --network liquidv1 \
             --out my_utxos.json \
             --esplora https://blockstream.info/liquid/api \
             --delay-ms 120
```

**Options**

| Option         | Description                        | Default                                                                    |
| -------------- | ---------------------------------- | -------------------------------------------------------------------------- |
| `--mnemonic`   | BIP39 mnemonic words               | required                                                                   |
| `--network`    | `liquidv1` or `testnet`            | liquidv1                                                                   |
| `--out` / `-o` | Output JSON file                   | utxos.json                                                                 |
| `--esplora`    | Esplora API base URL               | [https://blockstream.info/liquid/api](https://blockstream.info/liquid/api) |
| `--delay-ms`   | Min milliseconds between API calls | 100                                                                        |

The output JSON conforms to **schema v2 (`ssutxos-2`)** and includes both spent and unspent UTXOs.

---

### Compare Snapshots

```bash
ssutxos compare utxosA.json utxosB.json \
                --esplora https://blockstream.info/liquid/api \
                --delay-ms 120
```

**Example output**

```
Starting from utxos1.json utxos.
Searching in utxos2.json-derived utxos 0 hops out...
  new utxos encountered in this round: 12
  nothing found
Searching in utxos2.json-derived utxos 1 hops out...
  new utxos encountered in this round: 37
  FOUND a utxo: abcd1234...:0
...
```

The search continues indefinitely until you press **Ctrl-C**.

---

## JSON Schema v2 (`ssutxos-2`)

```json
{
  "schema": "ssutxos-2",
  "network": "liquidv1",
  "generated_at": "2025-08-18T00:00:00Z",
  "wallet": {
    "source": "mnemonic",
    "descriptor": null
  },
  "utxos": [
    {
      "id": "txid:vout",
      "status": "unspent",
      "txid": "hex",
      "vout": 0,
      "address": "string",
      "script_pubkey": "hex",
      "asset": "LBTC",
      "amount_sat": 12345,
      "block_height": 1234,
      "block_time": 1700000000,
      "spending_txid": null,
      "spending_block_time": null,
      "metadata": {}
    }
  ]
}
```

---

## Quick Start Example

If you don’t have a mnemonic yet, you can try the `compare` command using two small dummy snapshots:

```bash
# Create example snapshots
echo '{
  "schema": "ssutxos-2",
  "network": "liquidv1",
  "generated_at": "2025-08-18T00:00:00Z",
  "wallet": {"source": "example"},
  "utxos": [{"id": "deadbeef:0", "status": "unspent", "txid": "deadbeef", "vout": 0, "address": null, "asset": "LBTC", "amount_sat": 1000}]
}' > a.json

cp a.json b.json

# Run compare
ssutxos compare a.json b.json --esplora https://blockstream.info/liquid/api --delay-ms 200
```

---

## Development

Run locally from source:

```bash
python -m ssutxos --help
```

Run tests:

```bash
pytest -q
```

---

## License

MIT License © 2025

