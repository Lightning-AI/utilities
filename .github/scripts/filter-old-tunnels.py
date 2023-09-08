import os
from datetime import datetime, timedelta

import fire


def main(input_file: str, delay_hours: float = 1, pattern: str = "") -> None:
    assert os.path.isfile(input_file), f"missing file {input_file}"
    with open(input_file, encoding="utf8") as fp:
        lines = [ln.strip().split("|") for ln in fp.readlines()]

    # Parse table with tunnels
    tunnels = [
        dict(name=ln[0].strip(),
             created_at=datetime.fromisoformat(ln[1].strip()[:-1]))
        for ln in lines
    ]

    # Define the threshold for one hour
    hours_ago = datetime.now() - timedelta(hours=delay_hours)

    # Filter the names based on the time
    old_tunnels = [
        tl["name"] for tl in tunnels if tl["created_at"] < hours_ago
    ]
    if pattern:
        old_tunnels = [tl for tl in old_tunnels if pattern in tl]
    if old_tunnels:
        print(os.linesep.join(old_tunnels))


if __name__ == '__main__':
    fire.Fire(main)
