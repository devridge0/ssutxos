import typer
from .utils import load_json, save_json
from .explorer import EsploraClient

app = typer.Typer(help="Enrich a UTXO JSON with spent info.")

@app.command()
def run(
    src_json: str,
    out_json: str = typer.Option(None, "--out"),
    api_base: str = typer.Option("https://blockstream.info/liquid/api", "--api-base"),
    sleep_ms: int = typer.Option(100, "--sleep-ms"),
):
    data = load_json(src_json)

    # Accept both list and {"utxos":[...]}
    if isinstance(data, dict) and "utxos" in data:
        items = data["utxos"]
        wrapper = True
    elif isinstance(data, list):
        items = data
        wrapper = False
    else:
        raise typer.BadParameter("Input JSON must be a list or contain a 'utxos' array.")

    api = EsploraClient(base_url = api_base, sleep_ms = sleep_ms)

    for u in items:
        outsp = api.get_outspend(u["txid"], int(u["vout"]))
        u["spent"] = bool(outsp and outsp.get("spent"))
        if u["spent"]:
            u["spent_by_txid"] = outsp.get("txid")
            u["spent_vin"] = outsp.get("vin")
            u["spent_status"] = outsp.get("status")

    dst = out_json or src_json
    if wrapper:
        data["utxos"] = items
        save_json(data, dst)
    else:
        save_json(items, dst)

    typer.echo(f"Enriched JSON saved to {dst}")
