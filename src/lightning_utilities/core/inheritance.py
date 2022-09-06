from typing import Type, Set, Iterator


def get_all_subclasses_iterator(cls: Type) -> Iterator[Type]:
    def recurse(cl: Type) -> None:
        for subclass in cl.__subclasses__():
            yield subclass
            yield from recurse(subclass)
    yield from recurse(cls)


def get_all_subclasses(cls: Type) -> Set[Type]:
    return set(get_all_subclasses_iterator(cls))
