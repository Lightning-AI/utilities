from lightning_utilities.core.enums import StrEnum


class MyEnum(StrEnum):
    FOO = "FOO"
    BAR = "BAR"
    BAZ = "BAZ"
    NUM = "32"


def test_consistency():
    # normal equality, case invariant
    assert MyEnum.FOO == "FOO"
    assert MyEnum.FOO == "foo"

    # int support
    assert MyEnum.NUM == 32
    assert MyEnum.NUM in (32, "32")

    # key-based
    assert MyEnum.NUM == MyEnum.from_str("num")

    # collections
    assert MyEnum.BAZ not in ("FOO", "BAR")
    assert MyEnum.BAZ in ("FOO", "BAZ")
    assert MyEnum.BAZ in ("baz", "FOO")
    assert MyEnum.BAZ not in {"BAR", "FOO"}
    # hash cannot be case invariant
    assert MyEnum.BAZ not in {"BAZ", "FOO"}
    assert MyEnum.BAZ in {"baz", "FOO"}