import fire

from pl_devtools.dependencies import requirements_prune_pkgs, replace_oldest_ver


def _PrintResult(component_trace, verbose=False):
    pass


# Patch: fire cli displays help text if the object is not printable
fire.core._PrintResult = _PrintResult


def main():
    fire.Fire({
        'requirements_prune_pkgs': requirements_prune_pkgs,
        'replace_oldest_ver': replace_oldest_ver,})


if __name__ == "__main__":
    main()
