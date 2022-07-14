import fire

from pl_devtools.dependencies import replace_oldest_ver, requirements_prune_pkgs


def main() -> None:
    fire.Fire(
        {
            "requirements": {
                "prune-pkgs": requirements_prune_pkgs,
                "set-oldest": replace_oldest_ver,
            }
        }
    )


if __name__ == "__main__":
    main()
