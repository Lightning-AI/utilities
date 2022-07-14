import fire

from pl_devtools.dependencies import replace_oldest_ver, requirements_prune_pkgs


def _PrintResult(component_trace, verbose=False):
    pass


# Patch: fire cli displays help text if the object is not printable
fire.core._PrintResult = _PrintResult


def main():
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
