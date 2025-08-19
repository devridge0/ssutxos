"""This module provides the RP To-Do CLI."""
# ssutxos/cli.py
from typing import Optional
import json
import typer
from lwk import Network, Mnemonic, Signer, Wollet, Chain
from ssutxos import __app_name__, __version__

from . import compare, enrich

app = typer.Typer()

# ---------------------------
# Sideswap asset mapping
# ---------------------------
SIDESWAP_ASSETS = {
    "6f0279e9ed041c3d710a9f57d0c02928416460c4b722ae3457a11eec381c526d": "L-BTC",
    "ce091c998b83c78bb71a632313ba3760f1763d9cfcffae02258ffa9865a37bd2": "USDt",
    "18729918ab4bca843656f08d4dd877bed6641fbd596a0a963abbf199cfeb3cec": "EURx",
    "06d1085d6a3a1328fb8189d106c7a8afbef3d327e34504828c4cac2c74ac0802": "SSWP",
    "aa909f1b77451e409fe95fe1d3638ad017ab3325c6d4f00301af6d582d0f2034": "BMN2"
}

# ---------------------------
# Version callback
# ---------------------------
def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True,
    )
) -> None:
    pass

# Add subcommands from modules
app.add_typer(compare.app, name="compare")
app.add_typer(enrich.app, name="enrich")

# ---------------------------
# Helper: Save JSON
# ---------------------------
def save_json(data, output_file: str = "utxos.json") -> None:
    with open(output_file, "w") as f:
        json.dump(data, f, indent=4)
    typer.echo(f"✅ Saved JSON: {output_file}")

# ---------------------------
# Helper: Initialize wallet
# ---------------------------
def init_wallet(mnemonic: str, network: str) -> Wollet:
    net = Network.mainnet() if network == "mainnet" else Network.testnet()
    signer = Signer(Mnemonic(mnemonic), net)
    descriptor = signer.wpkh_slip77_descriptor()
    wallet = Wollet(net, descriptor, datadir=None)
    client = net.default_electrum_client()
    client.ping()
    update = client.full_scan(wallet)
    wallet.apply_update(update)
    return wallet

# ---------------------------
# CLI command: list
# ---------------------------
@app.command("list")
def list_utxos(
    mnemonic: str = typer.Option(..., "--mnemonic", "-mn", help="BIP39 mnemonic (12 or 24 words)"),
    network: str = typer.Option("mainnet", help="Liquid network", case_sensitive=False),
    output_file: str = typer.Option("utxos.json", "--output", "-o", help="Output JSON file")
):
    """
    List Liquid UTXOs for a wallet from mnemonic.
    """
    network = network.lower()
    if network not in ["mainnet", "testnet"]:
        typer.echo("❌ Invalid network. Choose 'mainnet' or 'testnet'.")
        raise typer.Exit(code=1)

    wallet = init_wallet(mnemonic, network)
    utxos = wallet.utxos()

    output = []
    for utxo in utxos:
        op = utxo.outpoint()
        unblinded = utxo.unblinded()  # TxOutSecrets object
        asset_id = unblinded.asset()
        amount = unblinded.value()

        coin_type = SIDESWAP_ASSETS.get(asset_id, asset_id)
        if coin_type == "L-BTC":
            balance = amount / 100_000_000
        else:
            balance = amount

        output.append({
            "txid": str(op.txid()),
            "vout": op.vout(),
            "asset": coin_type,
            "amount": balance,
            "address": str(utxo.address())
        })

    save_json(output, output_file)
    typer.echo(f"✅ Total UTXOs extracted: {len(utxos)}")

def run():
    app()

def main():
    app()