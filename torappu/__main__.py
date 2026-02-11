import sys

import anyio
import click

from torappu import __version__
from torappu.log import logger

from .models import Version


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(
    __version__,
    "-v",
    "--version",
    prog_name="torappu",
    message="%(prog)s: version %(version)s",
)
@click.argument("client_version")
@click.argument("res_version")
@click.option("-c", "--prev-client-version", help="prev client version")
@click.option("-r", "--prev-res-version", help="prev res version")
@click.option(
    "-e", "--exclude", help="excluded tasks, if specified, these tasks will be excluded"
)
@click.option(
    "-i", "--include", help="included tasks, if specified, only these tasks will be run"
)
def cli(
    client_version: str,
    res_version: str,
    prev_client_version: str | None,
    prev_res_version: str | None,
    exclude: str | None,
    include: str | None,
):
    from torappu.core import init_sentry, main

    init_sentry(headless=True)

    version = Version(res_version=res_version, client_version=client_version)
    prev = (
        Version(res_version=prev_res_version, client_version=prev_client_version)
        if prev_client_version and prev_res_version
        else None
    )

    logger.info(f"Remote version: {version!r}, Local version: {prev!r}")

    anyio.run(
        main,
        version,
        prev,
        (exclude and exclude.split(",")) or [],
        (include and include.split(",")) or [],
    )


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        sys.exit(1)
