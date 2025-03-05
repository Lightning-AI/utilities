# Copyright The Lightning AI team.
# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#

import lightning_utilities
from lightning_utilities.cli.dependencies import prune_pkgs_in_requirements, replace_oldest_ver


def _get_version() -> None:
    """Prints the version of the lightning_utilities package."""
    print(lightning_utilities.__version__)


def main() -> None:
    """CLI entry point."""
    from jsonargparse import CLI

    CLI({
        "requirements": {
            "_help": "Manage requirements files.",
            "prune-pkgs": prune_pkgs_in_requirements,
            "set-oldest": replace_oldest_ver,
        },
        "version": _get_version
    })


if __name__ == "__main__":
    main()
