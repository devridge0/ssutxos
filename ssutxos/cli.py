
from __future__ import annotations
import json, sys
from pathlib import Path
import typer

from .schemas import Snapshot, UTXO, SCHEMA_ID
from .compare import compare_loop

app = typer.Typer(help="ssutxos: Liquid UTXO tools")

def version_callback(value: bool):
    if value:
        from . import __app_name__, __version__
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: bool = typer.Option(None, "--version", callback=version_callback, is_eager=True, help="Show version and exit.")
):
    pass

@app.command(help="List utxos (unspent and spent) and save snapshot JSON (schema v2).")
def list(
    mnemonic: str = typer.Option(..., "--mnemonic", help="BIP39 mnemonic (spaces allowed)."),
    network: str = typer.Option("liquidv1", "--network", help="liquidv1 or testnet"),
    out: Path = typer.Option(Path("utxos.json"), "--out", "-o", help="Output JSON file"),
):
    # Placeholder implementation: user will wire up LWK or Esplora here.
    # For now, emit an empty snapshot so downstream commands can be exercised.
    snap = Snapshot.new(network=network, wallet={"source": "mnemonic"}, utxos=[])
    out.write_text(json.dumps(snap.to_json(), indent=2))
    typer.echo(f"wrote {out} (schema={SCHEMA_ID})")

@app.command(help="Compare two snapshot JSON files and search for graph connections, expanding outward indefinitely until Ctrl-C.")
def compare(
    utxos1: Path = typer.Argument(..., exists=True, readable=True),
    utxos2: Path = typer.Argument(..., exists=True, readable=True),
    esplora: str = typer.Option("https://blockstream.info/liquid/api", "--esplora", help="Esplora base URL"),
    delay_ms: int = typer.Option(100, "--delay-ms", min=0, help="Min milliseconds between API calls"),
):
    s1 = json.loads(utxos1.read_text())
    s2 = json.loads(utxos2.read_text())
    compare_loop(s1, s2, esplora_base=esplora, delay_ms=delay_ms)

def app_entry():
    app()

if __name__ == "__main__":
    app_entry()



@app.command(help="List utxos (unspent and spent) using LWK and save snapshot JSON (schema v2).")
def list(
    mnemonic: str = typer.Option(..., "--mnemonic", help="BIP39 mnemonic (quotes ok)."),
    network: str = typer.Option("liquidv1", "--network", help="liquidv1 or testnet"),
    out: Path = typer.Option(Path("utxos.json"), "--out", "-o", help="Output JSON file"),
    esplora: str = typer.Option("https://blockstream.info/liquid/api", "--esplora", help="Esplora base URL (used to check spends)"),
    delay_ms: int = typer.Option(100, "--delay-ms", min=0, help="Min milliseconds between API calls to Esplora"),
):
    """
    Uses LWK Wollet to derive the wallet UTXOs. If LWK does not expose spend state,
    we consult Esplora /tx/<txid>/outspend/<vout> to mark spent UTXOs.
    """
    from lwk import Network as LwkNetwork, Mnemonic as LwkMnemonic, Signer as LwkSigner, Wollet as LwkWollet
    from .schemas import UTXO, Snapshot
    from .providers import EsploraProvider

    net = LwkNetwork.MAINNET if network == "liquidv1" else LwkNetwork.TESTNET
    # Build wallet
    mn = LwkMnemonic.from_mnemonic(mnemonic)
    signer = LwkSigner.from_mnemonic(mn)
    w = LwkWollet(signer=signer, network=net)

    # Sync wallet (if applicable)
    if hasattr(w, "sync"):
        try:
            w.sync()
        except Exception:
            pass

    # Fetch UTXOs with as much info as possible
    # We try multiple method names to be robust against LWK versions.
    utxo_rows = []
    if hasattr(w, "utxos"):
        try:
            utxo_rows = w.utxos(include_spent=True)  # preferred
        except TypeError:
            utxo_rows = w.utxos()  # maybe returns only unspent
    elif hasattr(w, "listunspent"):
        utxo_rows = w.listunspent()
    else:
        raise RuntimeError("LWK wallet does not expose a UTXO listing method (expected .utxos or .listunspent).")

    provider = EsploraProvider(esplora, delay_ms)

    def get_field(o, *names, default=None):
        for n in names:
            if isinstance(o, dict) and n in o:
                return o[n]
            if hasattr(o, n):
                return getattr(o, n)
        return default

    utxos: list[UTXO] = []
    for row in utxo_rows:
        txid = get_field(row, "txid", "tx_hash", default=None)
        vout = get_field(row, "vout", "n", default=None)
        address = get_field(row, "address", default=None)
        script_pubkey = get_field(row, "script_pubkey", "script", default=None)
        asset = get_field(row, "asset", "asset_id", default=None)
        amount_sat = get_field(row, "amount_sat", "amount", "value", default=0)
        block_height = get_field(row, "block_height", "height", default=None)
        block_time = get_field(row, "block_time", "time", default=None)

        if txid is None or vout is None:
            # Skip malformed entries
            continue

        # Determine spent status
        spent = get_field(row, "spent", default=None)
        spending_txid = get_field(row, "spending_txid", default=None)
        spending_block_time = get_field(row, "spending_block_time", default=None)

        # If LWK didn't provide spent state, query esplora
        if spent is None:
            try:
                outspend = provider.tx_outspend(txid, int(vout))
                spent = bool(outspend.get("spent"))
                spending_txid = outspend.get("txid")
            except Exception:
                spent = False
        if spending_txid and spending_block_time is None:
            # Try to get spending tx time
            try:
                stx = provider.tx(spending_txid)
                # Best-effort; esplora returns status.block_time sometimes
                spending_block_time = get_field(stx, "status", default={}, ).get("block_time")
            except Exception:
                pass

        status = "spent" if spent else "unspent"

        utxos.append(UTXO(
            id=f"{txid}:{int(vout)}",
            status=status,
            txid=txid,
            vout=int(vout),
            address=address,
            script_pubkey=script_pubkey,
            asset=asset,
            amount_sat=int(amount_sat) if amount_sat is not None else 0,
            block_height=int(block_height) if block_height is not None else None,
            block_time=int(block_time) if block_time is not None else None,
            first_seen=None,
            last_seen=None,
            spending_txid=spending_txid,
            spending_block_time=spending_block_time,
            metadata={},
        ))

    snap = Snapshot.new(network=network, wallet={"source": "mnemonic"}, utxos=utxos)
    out.write_text(json.dumps(snap.to_json(), indent=2))
    typer.echo(f"wrote {out} (schema={SCHEMA_ID}, utxos={len(utxos)})")

