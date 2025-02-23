import dataclasses
import numbers
from collections import OrderedDict, defaultdict, namedtuple
from dataclasses import InitVar
from functools import cached_property
from typing import Any, ClassVar, Optional

import pytest
from unittests.mocks import torch

from lightning_utilities.core.apply_func import apply_to_collection, apply_to_collections

_TENSOR_0 = torch.tensor(0)
_TENSOR_1 = torch.tensor(1)


@dataclasses.dataclass
class Feature:
    input_ids: torch.Tensor
    segment_ids: torch.Tensor

    def __eq__(self, o: object) -> bool:
        """Perform equal operation."""
        if not isinstance(o, Feature):
            return NotImplemented
        return torch.equal(self.input_ids, o.input_ids) and torch.equal(self.segment_ids, o.segment_ids)


@dataclasses.dataclass
class ModelExample:
    example_ids: list[str]
    feature: Feature
    label: torch.Tensor
    some_constant: int = dataclasses.field(init=False)

    def __post_init__(self):
        self.some_constant = 7

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, ModelExample):
            return NotImplemented

        return (
            self.example_ids == o.example_ids
            and self.feature == o.feature
            and torch.equal(self.label, o.label)
            and self.some_constant == o.some_constant
        )


@dataclasses.dataclass
class WithClassVar:
    class_var: ClassVar[int] = 0
    dummy: Any

    def __eq__(self, o: object) -> bool:
        """Perform equal operation."""
        if not isinstance(o, WithClassVar):
            return NotImplemented
        if isinstance(self.dummy, torch.Tensor):
            return torch.equal(self.dummy, o.dummy)

        return self.dummy == o.dummy


@dataclasses.dataclass
class WithInitVar:
    dummy: Any
    override: InitVar[Optional[Any]] = None

    def __post_init__(self, override: Optional[Any]):
        if override is not None:
            self.dummy = override

    def __eq__(self, o: object) -> bool:
        if not isinstance(o, WithInitVar):
            return NotImplemented
        if isinstance(self.dummy, torch.Tensor):
            return torch.equal(self.dummy, o.dummy)

        return self.dummy == o.dummy


@dataclasses.dataclass
class WithClassAndInitVar:
    class_var: ClassVar[torch.Tensor] = _TENSOR_0
    dummy: Any
    override: InitVar[Optional[Any]] = _TENSOR_1

    def __post_init__(self, override: Optional[Any]):
        if override is not None:
            self.dummy = override

    def __eq__(self, o: object) -> bool:
        """Equal."""
        if not isinstance(o, WithClassAndInitVar):
            return NotImplemented
        if isinstance(self.dummy, torch.Tensor):
            return torch.equal(self.dummy, o.dummy)

        return self.dummy == o.dummy


class _CustomCollection(dict):
    def __init__(self, initial_dict) -> None:
        super().__init__(initial_dict)


ntc = namedtuple("Foo", ["bar", "baz"])


def test_recursive_application_to_collection():
    model_example = ModelExample(
        example_ids=["i-1", "i-2", "i-3"],
        feature=Feature(input_ids=torch.tensor([1.0, 2.0, 3.0]), segment_ids=torch.tensor([4.0, 5.0, 6.0])),
        label=torch.tensor([7.0, 8.0, 9.0]),
    )

    to_reduce = {
        "a": torch.tensor([1.0]),  # Tensor
        "b": [torch.tensor([2.0])],  # list
        "c": (torch.tensor([100.0]),),  # tuple
        "d": ntc(bar=5.0, baz=10.0),  # named tuple
        "f": "this_is_a_dummy_str",  # string
        "g": 12.0,  # number
        "h": Feature(input_ids=torch.tensor([1.0, 2.0, 3.0]), segment_ids=torch.tensor([4.0, 5.0, 6.0])),  # dataclass
        "i": model_example,  # nested dataclass
        "j": WithClassVar(torch.arange(3)),  # dataclass with class variable
        "k": WithInitVar("this_gets_overridden", torch.tensor([2.0])),  # dataclass with init-only variable
        "l": WithClassAndInitVar(model_example, None),  # nested dataclass with class and init-only variables
    }

    model_example_result = ModelExample(
        example_ids=["i-1", "i-2", "i-3"],
        feature=Feature(input_ids=torch.tensor([2.0, 4.0, 6.0]), segment_ids=torch.tensor([8.0, 10.0, 12.0])),
        label=torch.tensor([14.0, 16.0, 18.0]),
    )

    expected_result = {
        "a": torch.tensor([2.0]),
        "b": [torch.tensor([4.0])],
        "c": (torch.tensor([200.0]),),
        "d": ntc(bar=10, baz=20),
        "f": "this_is_a_dummy_str",
        "g": 24.0,
        "h": Feature(input_ids=torch.tensor([2.0, 4.0, 6.0]), segment_ids=torch.tensor([8.0, 10.0, 12.0])),
        "i": model_example_result,
        "j": WithClassVar(torch.arange(0, 6, 2)),
        "k": WithInitVar(torch.tensor([4.0])),
        "l": WithClassAndInitVar(model_example_result, None),
    }

    reduced = apply_to_collection(to_reduce, (torch.Tensor, numbers.Number), lambda x: x * 2)

    assert isinstance(reduced, dict), "Type Consistency of dict not preserved"
    assert all(x in reduced for x in to_reduce), "Not all entries of the dict were preserved"
    assert all(isinstance(reduced[k], type(expected_result[k])) for k in to_reduce), (
        "At least one type was not correctly preserved"
    )

    assert isinstance(reduced["a"], torch.Tensor), "Reduction Result of a Tensor should be a Tensor"
    assert torch.equal(expected_result["a"], reduced["a"]), "Reduction of a tensor does not yield the expected value"

    assert isinstance(reduced["b"], list), "Reduction Result of a list should be a list"
    assert all(torch.equal(x, y) for x, y in zip(reduced["b"], expected_result["b"])), (
        "At least one value of list reduction did not come out as expected"
    )

    assert isinstance(reduced["c"], tuple), "Reduction Result of a tuple should be a tuple"
    assert all(torch.equal(x, y) for x, y in zip(reduced["c"], expected_result["c"])), (
        "At least one value of tuple reduction did not come out as expected"
    )

    assert isinstance(reduced["d"], ntc), "Type Consistency for named tuple not given"
    assert isinstance(reduced["d"].bar, numbers.Number), (
        "Failure in type promotion while reducing fields of named tuples"
    )
    assert reduced["d"].bar == expected_result["d"].bar

    assert isinstance(reduced["f"], str), "A string should not be reduced"
    assert reduced["f"] == expected_result["f"], "String not preserved during reduction"

    assert isinstance(reduced["g"], numbers.Number), "Reduction of a number should result in a number"
    assert reduced["g"] == expected_result["g"], "Reduction of a number did not yield the desired result"

    def _assert_dataclass_reduction(actual, expected, dataclass_type: str = ""):
        assert dataclasses.is_dataclass(actual), (
            f"Reduction of a {dataclass_type} dataclass should result in a dataclass"
        )
        assert not isinstance(actual, type)
        for field in dataclasses.fields(actual):
            if dataclasses.is_dataclass(field.type):
                _assert_dataclass_reduction(getattr(actual, field.name), getattr(expected, field.name), "nested")
        assert actual == expected, f"Reduction of a {dataclass_type} dataclass did not yield the desired result"

    _assert_dataclass_reduction(reduced["h"], expected_result["h"])

    _assert_dataclass_reduction(reduced["i"], expected_result["i"])

    dataclass_type = "ClassVar-containing"
    _assert_dataclass_reduction(reduced["j"], expected_result["j"], dataclass_type)
    assert WithClassVar.class_var == 0, f"Reduction of a {dataclass_type} dataclass should not change the class var"

    _assert_dataclass_reduction(reduced["k"], expected_result["k"], "InitVar-containing")

    dataclass_type = "Class-and-InitVar-containing"
    _assert_dataclass_reduction(reduced["l"], expected_result["l"], dataclass_type)
    assert torch.equal(WithClassAndInitVar.class_var, torch.tensor(0)), (
        f"Reduction of a {dataclass_type} dataclass should not change the class var"
    )


@pytest.mark.parametrize(
    ("ori", "target"),
    [
        (
            {"a": 1, "b": 2, "c": 3},
            {"a": "1", "b": "2", "c": "3"},
        ),
        (
            OrderedDict([("b", 2), ("a", 1), ("c", 3)]),
            OrderedDict([("b", "2"), ("a", "1"), ("c", "3")]),
        ),
        (
            _CustomCollection({"a": 1, "b": 2, "c": 3}),
            _CustomCollection({"a": "1", "b": "2", "c": "3"}),
        ),
        (
            defaultdict(int, {"a": 1, "b": 2, "c": 3}),
            defaultdict(int, {"a": "1", "b": "2", "c": "3"}),
        ),
        (
            ntc(bar=5, baz=5),
            ntc(bar="5", baz="5"),
        ),
    ],
)
def test_application_to_collection_return_type(ori, target):
    # custom mapping support
    reduced = apply_to_collection(ori, int, lambda x: str(x))
    assert reduced == target
    assert type(reduced) is type(target)


def test_apply_to_collection_include_none():
    to_reduce = [1, 2, 3.4, 5.6, 7, (8, 9.1, {10: 10})]

    def fn(x):
        if isinstance(x, float):
            return x
        return None

    reduced = apply_to_collection(to_reduce, (int, float), fn)
    assert reduced == [None, None, 3.4, 5.6, None, (None, 9.1, {10: None})]

    reduced = apply_to_collection(to_reduce, (int, float), fn, include_none=False)
    assert reduced == [3.4, 5.6, (9.1, {})]


def test_apply_to_collections():
    to_reduce_1 = {"a": {"b": [1, 2]}, "c": 5}
    to_reduce_2 = {"a": {"b": [3, 4]}, "c": 6}

    def fn(a, b):
        return a + b

    # basic test
    reduced = apply_to_collections(to_reduce_1, to_reduce_2, int, fn)
    assert reduced == {"a": {"b": [4, 6]}, "c": 11}

    with pytest.raises(KeyError):
        # strict mode - if a key does not exist in both we fail
        apply_to_collections({**to_reduce_2, "d": "foo"}, to_reduce_1, float, fn)

    # multiple dtypes
    reduced = apply_to_collections(to_reduce_1, to_reduce_2, (list, int), fn)
    assert reduced == {"a": {"b": [1, 2, 3, 4]}, "c": 11}

    # wrong dtype
    reduced = apply_to_collections(to_reduce_1, to_reduce_2, (list, int), fn, wrong_dtype=int)
    assert reduced == {"a": {"b": [1, 2, 3, 4]}, "c": 5}

    # list takes precedence because it is the type of data1
    reduced = apply_to_collections([1, 2, 3], [4], (int, list), fn)
    assert reduced == [1, 2, 3, 4]

    # different sizes
    with pytest.raises(ValueError, match="Sequence collections have different sizes"):
        apply_to_collections([[1, 2], [3]], [4], int, fn)

    def fn(a, b):
        return a.keys() | b.keys()

    # base case
    reduced = apply_to_collections(to_reduce_1, to_reduce_2, dict, fn)
    assert reduced == {"a", "c"}

    # type conversion
    to_reduce = [(1, 2), (3, 4)]
    reduced = apply_to_collections(to_reduce, to_reduce, int, lambda *x: sum(x))
    assert reduced == [(2, 4), (6, 8)]

    # named tuple
    foo = namedtuple("Foo", ["bar"])
    to_reduce = [foo(1), foo(2), foo(3)]
    reduced = apply_to_collections(to_reduce, to_reduce, int, lambda *x: sum(x))
    assert reduced == [foo(2), foo(4), foo(6)]

    # passing none
    reduced1 = apply_to_collections([1, 2, 3], None, int, lambda x: x * x)
    reduced2 = apply_to_collections(None, [1, 2, 3], int, lambda x: x * x)
    assert reduced1 == reduced2 == [1, 4, 9]
    reduced = apply_to_collections(None, None, int, lambda x: x * x)
    assert reduced is None


def test_apply_to_collections_dataclass():
    to_reduce_1 = Feature(input_ids=torch.tensor([1.0, 2.0, 3.0]), segment_ids=torch.tensor([4.0, 5.0, 6.0]))
    to_reduce_2 = Feature(input_ids=torch.tensor([1.0, 2.0, 3.0]), segment_ids=torch.tensor([4.0, 5.0, 6.0]))

    def fn(a, b):
        return a + b

    reduced = apply_to_collections(to_reduce_1, to_reduce_2, torch.Tensor, fn)
    assert reduced == Feature(input_ids=torch.tensor([2.0, 4.0, 6.0]), segment_ids=torch.tensor([8.0, 10.0, 12.0]))

    model_example = ModelExample(
        example_ids=["i-1", "i-2", "i-3"],
        feature=to_reduce_1,
        label=torch.tensor([7.0, 8.0, 9.0]),
    )

    # different types
    with pytest.raises(TypeError, match="Expected inputs to be dataclasses of the same type"):
        apply_to_collections(to_reduce_1, [1, 2], torch.Tensor, fn)

    # unmatched fields
    with pytest.raises(TypeError, match="Dataclasses fields do not match"):
        apply_to_collections(to_reduce_1, model_example, torch.Tensor, fn)

    classvar = WithClassVar(torch.arange(3))  # dataclass with same number but different type of fields
    with pytest.raises(TypeError, match="Dataclasses fields do not match"):
        apply_to_collections(to_reduce_1, classvar, torch.Tensor, fn)


def test_apply_to_collection_frozen_dataclass():
    @dataclasses.dataclass(frozen=True)
    class Foo:
        var: int

    foo = Foo(0)
    with pytest.raises(ValueError, match="frozen dataclass was passed"):
        apply_to_collection(foo, int, lambda x: x + 1)


def test_apply_to_collection_allow_frozen_dataclass():
    @dataclasses.dataclass(frozen=True)
    class Foo:
        var: int

    foo = Foo(0)
    result = apply_to_collection(foo, int, lambda x: x + 1, allow_frozen=True)
    assert foo == result


def test_apply_to_collection_with_cached_property_dataclass():
    @dataclasses.dataclass
    class Foo:
        var: torch.Tensor

        @cached_property
        def cached_property(self):
            return self.var * 2

    foo = Foo(torch.tensor(1))
    assert torch.equal(foo.cached_property, torch.tensor(2))
    result = apply_to_collection(foo, torch.Tensor, lambda x: x.add_(3))
    assert torch.equal(result.var, torch.tensor(4))
    assert torch.equal(result.cached_property, torch.tensor(8))
