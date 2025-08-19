# A CLI tool to inspect SideSwap UTXOs

`ssutxos` is a Python command-line interface (CLI) tool for interacting with Liquid wallets.
It allows users to list UTXOs (unspent transaction outputs) for a wallet derived from a BIP39 mnemonic, save them in JSON format, and compare different UTXO sets by exploring transaction descendants via the Blockstream Esplora API.

---

## ✨ Features

* Display the version of the CLI.
* List Liquid UTXOs for a wallet from a mnemonic.
* Support for both `mainnet` and `testnet` Liquid networks.
* Save UTXOs as a JSON file for further processing.
* Compare two UTXO sets and trace descendant relationships via transaction graph traversal.

---

## 📦 Installation

```bash
git clone https://github.com/devridge0/ssutxos.git
cd ssutxos
python -m venv lwk-venv
source lwk-venv/bin/activate
pip install -r requirements.txt

pip install -e .
```

---

## 🚀 Usage

### Show Version

```bash
ssutxos --version
```

Output:

```
ssutxos v1.0.0
```

---

### List UTXOs

```bash
ssutxos list --mnemonic "your twelve or twenty-four word mnemonic" --network mainnet
```

#### Options

| Option               | Description                            | Default |
| -------------------- | -------------------------------------- | ------- |
| `--mnemonic` / `-mn` | BIP39 mnemonic (12 or 24 words)        | None    |
| `--network`          | Liquid network: `mainnet` or `testnet` | mainnet |
| `--output`   / `-o`  | Output JSON file                       | utxos.json| 

#### Example

```bash
ssutxos list --mnemonic/-mn "abandon abandon abandon ..." --network testnet --output/-o utxos.json
```

This will output UTXOs in a JSON format like:

```json
[
  {
    "txid": "abc123...",
    "vout": 0,
    "asset": "L-BTC",
    "amount": 0.1234,
    "address": "ex1q..."
  }
]
```

Additionally, it saves the UTXOs to a file named `utxos.json`.

---

### Compare Two UTXO Sets

You can compare UTXOs from two JSON files.

```bash
ssutxos compare run utxos1.json utxos2.json --sleep-ms 100
```

* **utxos1.json** → the target UTXOs
* **utxos2.json** → starting UTXOs (the exploration frontier)
* `--sleep-ms` → delay between API requests (default: 100 ms, helps avoid rate limits)

#### Supported JSON Formats

Both wrapped and flat formats are accepted:

**Wrapped**

```json
{
  "utxos": [
    { "txid": "abc123...", "vout": 0, "asset": "L-BTC", "amount": 0.0001, "address": "lq1..." }
  ]
}
```

**Flat**

```json
[
  { "txid": "abc123...", "vout": 0, "asset": "L-BTC", "amount": 0.0001, "address": "lq1..." }
]
```

#### Example Run

```
Starting from utxos1.json utxos.
Searching in utxos2.json-derived descendants.
Targets: 2; Start frontier: 2
API base: https://blockstream.info/liquid/api; sleep: 100 ms
Searching hop 0: new frontier size 2
Searching hop 1: new frontier size 5
FOUND a match at hop 2: Outpoint(txid=abc123..., vout=1)
Stopped by user. Total matches found: 1
```

---

## 🗂 Code Structure

* `ssutxos/cli.py` – Main CLI entrypoint.
* `ssutxos/explorer.py` – Esplora API client.
* `ssutxos/graph.py` – Graph utilities (outpoints, BFS traversal).
* `ssutxos/compare.py` – Compare UTXO sets via graph traversal.
* `ssutxos/enrich.py` – UTXO enrichment helpers.
* `ssutxos/utils.py` – JSON and helper utilities.

---

## ⚠️ Notes

* Ensure you have internet access to query the Blockstream Esplora Liquid API (`https://blockstream.info/liquid/api`).
* Exploration runs until you **press Ctrl-C**. Large graphs may consume significant resources.
* Only L-BTC (Liquid Bitcoin) is supported for balance calculation.

---

## 📜 License

MIT License © 2025
