import typer
import time
from .utils import load_json
from .graph import Outpoint, parse_outpoints, bfs_descendants
from .explorer import EsploraClient


app = typer.Typer(help="Compare two utxo sets for connections.")


@app.command("run")
def compare_entry(
    utxos1: str = typer.Argument(..., help="Path to first utxos.json file"),
    utxos2: str = typer.Argument(..., help="Path to second utxos.json file"),
    sleep_ms: int = typer.Option(100, help="Milliseconds to sleep between API calls"),
    api_base: str = typer.Option(
        "https://blockstream.info/liquid/api", help="Esplora API base URL"
    ),
):
    """
    Compare two extracted utxo files and search for connections.
    Loops infinitely until interrupted with Ctrl-C.
    """

    # Load both files
    j1 = load_json(utxos1)
    j2 = load_json(utxos2)

    # Build target set (we're searching for these)
    targets = set(parse_outpoints(j1))
    # Seed starting frontier (expansion will begin from here)
    start = parse_outpoints(j2)

    typer.echo("Starting from utxos1.json utxos.")
    typer.echo("Searching in utxos2.json-derived descendants.")
    typer.echo(f"Targets: {len(targets)}; Start frontier: {len(start)}")
    typer.echo(f"API base: {api_base}; sleep: {sleep_ms} ms")

    api = EsploraClient(base_url=api_base, sleep_ms=sleep_ms)
    found_total = 0

    # Define callback handlers
    def is_target(op: Outpoint) -> bool:
        return op in targets

    def on_found(op: Outpoint, hop: int) -> None:
        nonlocal found_total
        found_total += 1
        typer.echo(
            f"FOUND a utxo: {op.txid}:{op.vout} "
            f"(hops: {hop})"
        )

    def on_round_begin(hop: int) -> None:
        typer.echo(f"\nSearching in utxos2.json-derived utxos {hop} hops out...")

    def on_round_end(hop: int, processed: int, new_in_round: int) -> None:
        typer.echo(f"new utxos encountered in this round: {new_in_round}")
        if new_in_round == 0:
            typer.echo("nothing found")

    # Run BFS until user stops with Ctrl-C
    try:
        bfs_descendants(
            start,
            is_target,
            api,
            on_found,
            on_round_begin,
            on_round_end,
        )
    except KeyboardInterrupt:
        typer.echo(f"\nStopped by user. Total matches found: {found_total}")
        raise typer.Exit(code=0)
