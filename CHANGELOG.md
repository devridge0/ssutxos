# Changelog

All notable changes to **ssutxos** will be documented here.  
This project follows **semantic versioning**.

---

## [0.1.0] - 2025-08-18
### Added
- **Schema v2 (`ssutxos-2`)**
  - Introduced a new standardized JSON format for wallet snapshots.
  - Supports both **spent** and **unspent** UTXOs.
  - Added fields:  
    - `status` (`unspent` | `spent`)  
    - `spending_txid` and `spending_block_time` (for spent outputs)  
    - `metadata` extensible field  
  - Top-level fields include: `schema`, `network`, `generated_at`, `wallet`, `utxos`.

- **New `list` command**
  - Extracts UTXOs from a BIP39 mnemonic via **LWK Wollet**.  
  - Falls back to **Esplora API** to check whether outputs are spent.  
  - Outputs JSON conforming to schema v2.  

- **New `compare` command**
  - Compares two snapshot JSON files and **traverses the transaction graph** outward hop by hop.  
  - Detects when a UTXO from snapshot A connects to one in snapshot B.  
  - Runs indefinitely until **Ctrl-C** is pressed.  
  - Supports configurable API throttling via `--delay-ms`.

- **Documentation**
  - Updated `README.md` to reflect new schema v2, usage examples, and Esplora integration.
  - Added quick start example with dummy snapshots.

### Changed
- Project refactored from an earlier “to-do CLI” scaffold into a **Liquid Network UTXO tool**.
- `pyproject.toml` updated to point entrypoint to `ssutxos.cli:app_entry`.

### Deprecated
- Schema v1 JSON files (only unspent outputs) are no longer produced.  
  Existing tools should migrate to schema v2 (`ssutxos-2`).

---

## [0.0.x] - Pre-release
- Initial experiments and scaffold (`RP To-Do CLI`).
- Very basic `list` command (unspent only).
- No compare functionality.
