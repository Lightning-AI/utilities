import fire

from pl_devtools.dependencies import replace_oldest_ver, prune_pkgs_in_requirements


def main() -> None:
    fire.Fire(
        {
            "requirements": {
                "prune-pkgs": prune_pkgs_in_requirements,
                "set-oldest": replace_oldest_ver,
            }
        }
    )


if __name__ == "__main__":
    main()
