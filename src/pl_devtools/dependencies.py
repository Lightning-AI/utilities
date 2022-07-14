
def requirements_prune_pkgs(packages: Sequence[str], req_files: Sequence[str] = REQUIREMENT_FILES_ALL) -> None:
    """Remove some packages from given requirement files."""
    if isinstance(req_files, str):
        req_files = [req_files]
    for req in req_files:
        _prune_packages(req, packages)


def _prune_packages(req_file: str, packages: Sequence[str]) -> None:
    """Remove some packages from given requirement files."""
    with open(req_file) as fp:
        lines = fp.readlines()

    if isinstance(packages, str):
        packages = [packages]
    for pkg in packages:
        lines = [ln for ln in lines if not ln.startswith(pkg)]
    pprint(lines)

    with open(req_file, "w") as fp:
        fp.writelines(lines)


def _replace_min(fname: str) -> None:
    req = open(fname).read().replace(">=", "==")
    open(fname, "w").write(req)


def replace_oldest_ver(requirement_fnames: Sequence[str] = REQUIREMENT_FILES_ALL) -> None:
    """Replace the min package version by fixed one."""
    for fname in requirement_fnames:
        _replace_min(fname)