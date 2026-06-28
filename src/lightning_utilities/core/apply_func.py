# Copyright The Lightning AI team.
# Licensed under the Apache License, Version 2.0 (the "License");
#     http://www.apache.org/licenses/LICENSE-2.0
#
import dataclasses
from collections import OrderedDict, defaultdict
from collections.abc import Callable, Mapping, Sequence
from copy import deepcopy
from functools import cached_property
from typing import Any


def is_namedtuple(obj: object) -> bool:
    """Return True if the given object is a namedtuple instance.

    This checks for a tuple with the namedtuple-specific attributes `_asdict` and `_fields`.

    """
    # https://github.com/pytorch/pytorch/blob/v1.8.1/torch/nn/parallel/scatter_gather.py#L4-L8
    return isinstance(obj, tuple) and hasattr(obj, "_asdict") and hasattr(obj, "_fields")


def is_dataclass_instance(obj: object) -> bool:
    """Return True if the given object is a dataclass instance (not a dataclass type)."""
    # https://docs.python.org/3/library/dataclasses.html#module-level-decorators-classes-and-functions
    return dataclasses.is_dataclass(obj) and not isinstance(obj, type)


def is_dataclass_frozen(obj: object) -> bool:
    """Return True if the given object is a frozen dataclass instance."""
    # https://stackoverflow.com/a/75958306
    return getattr(getattr(obj, "__dataclass_params__", None), "frozen", False)


def _dataclass_has_init_vars(data: Any) -> bool:
    """Return True if the dataclass declares any ``InitVar`` (pseudo-)fields.

    ``InitVar`` fields are excluded from ``dataclasses.fields`` and their values are consumed by ``__post_init__``
    rather than stored on the instance, so a frozen dataclass that declares them cannot be reconstructed from its stored
    fields.

    """
    return any(f._field_type is dataclasses._FIELD_INITVAR for f in data.__dataclass_fields__.values())


def _reconstruct_frozen_dataclass(data: Any, apply_field: Callable[[Any], Any]) -> Any:
    """Reconstruct a frozen dataclass by applying ``apply_field`` to each ``init`` field's value.

    Frozen dataclasses cannot be mutated in place, so instead of the deepcopy-and-``setattr`` approach
    used for mutable dataclasses, a new instance is built from the (transformed) init fields. Fields
    with ``init=False`` are retained from the original instance and written back via
    ``object.__setattr__`` (this overrides whatever ``__post_init__`` derived during construction,
    keeping parity with the retain-old behavior of the mutable path).

    Raises:
        ValueError: If the frozen dataclass declares ``InitVar`` fields, which cannot be reconstructed.

    """
    if _dataclass_has_init_vars(data):
        raise ValueError(
            "A frozen dataclass with `InitVar` fields was passed to `apply_to_collection`(s)"
            " but this is not supported: such instances cannot be reconstructed."
        )
    init_fields = {}
    non_init_fields = {}
    for field in dataclasses.fields(data):
        field_value = getattr(data, field.name)
        if field.init:
            init_fields[field.name] = apply_field(field_value)
        else:
            non_init_fields[field.name] = field_value
    result = type(data)(**init_fields)
    for field_name, field_value in non_init_fields.items():
        object.__setattr__(result, field_name, field_value)
    return result


def apply_to_collection(
    data: Any,
    dtype: type | Any | tuple[type | Any],
    function: Callable,
    *args: Any,
    wrong_dtype: type | tuple[type, ...] | None = None,
    include_none: bool = True,
    **kwargs: Any,
) -> Any:
    """Recursively applies a function to all elements of a certain dtype.

    Args:
        data: the collection to apply the function to
        dtype: the given function will be applied to all elements of this dtype
        function: the function to apply
        *args: positional arguments (will be forwarded to calls of ``function``)
        wrong_dtype: the given function won't be applied if this type is specified and the given collections
            is of the ``wrong_dtype`` even if it is of type ``dtype``
        include_none: Whether to include an element if the output of ``function`` is ``None``.
        **kwargs: keyword arguments (will be forwarded to calls of ``function``)

    Returns:
        The resulting collection

    """
    if include_none is False or wrong_dtype is not None:
        # not worth implementing these on the fast path: go with the slower option
        return _apply_to_collection_slow(
            data,
            dtype,
            function,
            *args,
            wrong_dtype=wrong_dtype,
            include_none=include_none,
            **kwargs,
        )
    # fast path for the most common cases:
    if isinstance(data, dtype):  # single element
        return function(data, *args, **kwargs)
    if data.__class__ is list and all(isinstance(x, dtype) for x in data):  # 1d homogeneous list
        return [function(x, *args, **kwargs) for x in data]
    if data.__class__ is tuple and all(isinstance(x, dtype) for x in data):  # 1d homogeneous tuple
        return tuple(function(x, *args, **kwargs) for x in data)
    if data.__class__ is dict and all(isinstance(x, dtype) for x in data.values()):  # 1d homogeneous dict
        return {k: function(v, *args, **kwargs) for k, v in data.items()}
    # slow path for everything else
    return _apply_to_collection_slow(
        data,
        dtype,
        function,
        *args,
        wrong_dtype=wrong_dtype,
        include_none=include_none,
        **kwargs,
    )


def _apply_to_collection_slow(
    data: Any,
    dtype: type | Any | tuple[type | Any],
    function: Callable,
    *args: Any,
    wrong_dtype: type | tuple[type, ...] | None = None,
    include_none: bool = True,
    **kwargs: Any,
) -> Any:
    # Breaking condition
    if isinstance(data, dtype) and (wrong_dtype is None or not isinstance(data, wrong_dtype)):
        return function(data, *args, **kwargs)

    elem_type = type(data)

    # Recursively apply to collection items
    if is_dataclass_instance(data):
        if is_dataclass_frozen(data):
            # frozen dataclass: reconstruct a new instance from (transformed) init fields
            def _apply_field(field_value: Any) -> Any:
                v = _apply_to_collection_slow(
                    field_value,
                    dtype,
                    function,
                    *args,
                    wrong_dtype=wrong_dtype,
                    include_none=include_none,
                    **kwargs,
                )
                if not include_none and v is None:  # retain old value
                    v = field_value
                return v

            return _reconstruct_frozen_dataclass(data, _apply_field)

        # mutable dataclass: deepcopy + setattr (handles InitVar, init=False, and cached_property reset)
        # make a deepcopy of the data,
        # but do not deepcopy mapped fields since the computation would
        # be wasted on values that likely get immediately overwritten
        fields = {}
        memo = {}
        for field in dataclasses.fields(data):
            field_value = getattr(data, field.name)
            fields[field.name] = (field_value, field.init)
            memo[id(field_value)] = field_value
        result = deepcopy(data, memo=memo)
        # apply function to each field
        for field_name, (field_value, field_init) in fields.items():
            v = None
            if field_init:
                v = _apply_to_collection_slow(
                    field_value,
                    dtype,
                    function,
                    *args,
                    wrong_dtype=wrong_dtype,
                    include_none=include_none,
                    **kwargs,
                )
            if not field_init or (not include_none and v is None):  # retain old value
                v = getattr(data, field_name)
            setattr(result, field_name, v)

        # Explicitly resetting cached property.
        for cached_name in filter(
            lambda k: isinstance(getattr(type(data), k), cached_property), vars(type(data)).keys()
        ):
            vars(result).pop(cached_name, None)
        return result

    if isinstance(data, Mapping):
        out = []
        for k, v in data.items():
            v = _apply_to_collection_slow(
                v,
                dtype,
                function,
                *args,
                wrong_dtype=wrong_dtype,
                include_none=include_none,
                **kwargs,
            )
            if include_none or v is not None:
                out.append((k, v))
        if isinstance(data, defaultdict):
            return elem_type(data.default_factory, OrderedDict(out))
        return elem_type(OrderedDict(out))

    is_namedtuple_ = is_namedtuple(data)
    is_sequence = isinstance(data, Sequence) and not isinstance(data, str)
    if is_namedtuple_ or is_sequence:
        out = []
        for d in data:
            v = _apply_to_collection_slow(
                d,
                dtype,
                function,
                *args,
                wrong_dtype=wrong_dtype,
                include_none=include_none,
                **kwargs,
            )
            if include_none or v is not None:
                out.append(v)
        return elem_type(*out) if is_namedtuple_ else elem_type(out)

    # data is neither of dtype, nor a collection
    return data


def apply_to_collections(
    data1: Any | None,
    data2: Any | None,
    dtype: type | Any | tuple[type | Any],
    function: Callable,
    *args: Any,
    wrong_dtype: type | tuple[type] | None = None,
    **kwargs: Any,
) -> Any:
    """Zip two collections and apply a function to items of a certain dtype.

    Args:
        data1: The first collection. If ``None`` and ``data2`` is not ``None``, the arguments are swapped.
        data2: The second collection. May be ``None`` to apply ``function`` only to ``data1``.
        dtype: The type(s) for which the given ``function`` will be applied to matching elements.
        function: The function to apply to matching elements.
        *args: Positional arguments forwarded to calls of ``function``.
        wrong_dtype: If specified, ``function`` won't be applied to elements of this type even if they match ``dtype``.
        **kwargs: Keyword arguments forwarded to calls of ``function``.

    Returns:
        A collection with the same structure as the input where matching elements are transformed.

    Raises:
        ValueError: If sequence collections have different sizes, or if a frozen dataclass with ``InitVar``
            fields is passed.
        TypeError: If dataclass inputs are mismatched (different types or fields), or if ``data1`` is a
            dataclass instance but ``data2`` is not.

    """
    if data1 is None:
        if data2 is None:
            return None
        # in case they were passed reversed
        data1, data2 = data2, None

    elem_type = type(data1)

    if isinstance(data1, dtype) and data2 is not None and (wrong_dtype is None or not isinstance(data1, wrong_dtype)):
        return function(data1, data2, *args, **kwargs)

    if isinstance(data1, Mapping) and data2 is not None:
        # use union because we want to fail if a key does not exist in both
        zipped = {k: (data1[k], data2[k]) for k in data1.keys() | data2.keys()}
        return elem_type({
            k: apply_to_collections(*v, dtype, function, *args, wrong_dtype=wrong_dtype, **kwargs)
            for k, v in zipped.items()
        })

    is_namedtuple_ = is_namedtuple(data1)
    is_sequence = isinstance(data1, Sequence) and not isinstance(data1, str)
    if (is_namedtuple_ or is_sequence) and data2 is not None:
        if len(data1) != len(data2):
            raise ValueError("Sequence collections have different sizes.")
        out = [
            apply_to_collections(v1, v2, dtype, function, *args, wrong_dtype=wrong_dtype, **kwargs)
            for v1, v2 in zip(data1, data2)
        ]
        return elem_type(*out) if is_namedtuple_ else elem_type(out)

    if is_dataclass_instance(data1) and data2 is not None:
        if not is_dataclass_instance(data2):
            raise TypeError(
                "Expected inputs to be dataclasses of the same type or to have identical fields"
                f" but got input 1 of type {type(data1)} and input 2 of type {type(data2)}."
            )
        if not (
            len(dataclasses.fields(data1)) == len(dataclasses.fields(data2))
            and all(map(lambda f1, f2: isinstance(f1, type(f2)), dataclasses.fields(data1), dataclasses.fields(data2)))
        ):
            raise TypeError("Dataclasses fields do not match.")

        if is_dataclass_frozen(data1):
            # frozen dataclass: reconstruct from the zipped (transformed) init fields.
            # build a lookup of data2's fields so we can zip by position during reconstruction.
            fields2 = {field.name: getattr(data2, field.name) for field in dataclasses.fields(data2)}
            field_iter = iter(dataclasses.fields(data1))

            def _apply_field(field_value1: Any) -> Any:
                field = next(field_iter)
                return apply_to_collections(
                    field_value1,
                    fields2[field.name],
                    dtype,
                    function,
                    *args,
                    wrong_dtype=wrong_dtype,
                    **kwargs,
                )

            return _reconstruct_frozen_dataclass(data1, _apply_field)

        # make a deepcopy of the data,
        # but do not deepcopy mapped fields since the computation would
        # be wasted on values that likely get immediately overwritten
        data = [data1, data2]
        fields: list[dict] = [{}, {}]
        memo: dict = {}
        for i in range(len(data)):
            for field in dataclasses.fields(data[i]):
                field_value = getattr(data[i], field.name)
                fields[i][field.name] = (field_value, field.init)
                if i == 0:
                    memo[id(field_value)] = field_value

        result = deepcopy(data1, memo=memo)

        # apply function to each field
        for (field_name, (field_value1, field_init1)), (_, (field_value2, field_init2)) in zip(
            fields[0].items(), fields[1].items()
        ):
            v = None
            if field_init1 and field_init2:
                v = apply_to_collections(
                    field_value1,
                    field_value2,
                    dtype,
                    function,
                    *args,
                    wrong_dtype=wrong_dtype,
                    **kwargs,
                )
            if not field_init1 or not field_init2 or v is None:  # retain old value
                return apply_to_collection(data1, dtype, function, *args, wrong_dtype=wrong_dtype, **kwargs)
            setattr(result, field_name, v)
        return result

    return apply_to_collection(data1, dtype, function, *args, wrong_dtype=wrong_dtype, **kwargs)
