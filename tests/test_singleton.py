import threading
from dataclasses import dataclass
from itertools import product

import pytest

from simple_singleton import is_singleton, singleton
from simple_singleton.singleton import _SINGLETON_FLAG


def test_singleton_without_arguments():
    @singleton
    class BasicSingleton:
        def __init__(self, value) -> None:
            self.value = value

    instance1 = BasicSingleton("initial")
    instance2 = BasicSingleton("reassigned")
    assert instance1 is instance2
    assert instance2.value == "initial"

    @singleton
    class SubclassSingleton(BasicSingleton):
        pass

    with pytest.raises(
        TypeError,
        match=f"Singleton class {BasicSingleton.__name__} cannot be inherited",
    ):
        SubclassSingleton("reassigned")


@pytest.mark.parametrize(
    ("allow_subclass", "allow_reassignment"),
    list(product((False, False), repeat=2)),
)
def test_thread_safe_singleton(allow_subclass: bool, allow_reassignment: bool):
    @singleton(
        thread_safe=True,
        allow_subclass=allow_subclass,
        allow_reassignment=allow_reassignment,
    )
    class ThreadSafeSingleton:
        pass

    def create_instance(instances: list):
        instances.append(ThreadSafeSingleton())

    instances = []
    threads = [
        threading.Thread(target=create_instance, args=(instances,)) for _ in range(10)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert all(instance is instances[0] for instance in instances)


@pytest.mark.parametrize(
    ("thread_safe", "allow_reassignment"),
    list(product((True, False), repeat=2)),
)
def test_allow_subclass_singleton(thread_safe: bool, allow_reassignment: bool):
    @singleton(
        thread_safe=thread_safe,
        allow_subclass=True,
        allow_reassignment=allow_reassignment,
    )
    class ParentSingleton:
        pass

    @singleton
    class ChildSingleton(ParentSingleton):
        pass

    parent_instance = ParentSingleton()
    child_instance = ChildSingleton()

    assert parent_instance is not child_instance
    assert isinstance(parent_instance, ParentSingleton)
    assert isinstance(child_instance, ChildSingleton)


@pytest.mark.parametrize(
    ("thread_safe", "allow_reassignment"),
    list(product((True, False), repeat=2)),
)
def test_disallow_subclass_singleton(thread_safe: bool, allow_reassignment: bool):
    @singleton(
        thread_safe=thread_safe,
        allow_subclass=False,
        allow_reassignment=allow_reassignment,
    )
    class ParentSingleton:
        pass

    @singleton
    class ChildSingleton(ParentSingleton):
        pass

    with pytest.raises(
        TypeError,
        match=f"Singleton class {ParentSingleton.__name__} cannot be inherited",
    ):
        ChildSingleton()


@pytest.mark.parametrize(
    ("thread_safe", "allow_subclass"),
    list(product((True, False), repeat=2)),
)
def test_reassignment_singleton(thread_safe: bool, allow_subclass: bool):
    @singleton(
        thread_safe=thread_safe,
        allow_subclass=allow_subclass,
        allow_reassignment=True,
    )
    class ReassignableSingleton:
        def __init__(self, value):
            self.value = value

    instance1 = ReassignableSingleton("initial")
    instance1_id = id(instance1)

    instance2 = ReassignableSingleton("reassigned")
    instance2_id = id(instance2)

    assert instance1 is instance2
    assert instance1.value == "reassigned"
    # Check whether the instance id has changed since the reassignment
    assert instance1_id == instance2_id


@pytest.mark.parametrize(
    ("thread_safe", "allow_subclass"),
    list(product((True, False), repeat=2)),
)
def test_disallow_reassignment_singleton(thread_safe: bool, allow_subclass: bool):
    @singleton(
        thread_safe=thread_safe,
        allow_subclass=allow_subclass,
        allow_reassignment=False,
    )
    class NonReassignableSingleton:
        def __init__(self, value):
            self.value = value

    instance1 = NonReassignableSingleton("initial")
    instance1_id = id(instance1)

    instance2 = NonReassignableSingleton("reassigned")
    instance2_id = id(instance2)

    assert instance1 is instance2
    assert instance1.value == "initial"
    # Check whether the instance id has changed since the reassignment
    assert instance1_id == instance2_id


@pytest.mark.parametrize(
    ("allow_reassignment", "frozen_dataclass"),
    list(product((True, False), repeat=2)),
)
def test_singleton_with_dataclass(
    allow_reassignment: bool,
    frozen_dataclass: bool,
):
    @singleton(allow_reassignment=allow_reassignment)
    @dataclass(frozen=frozen_dataclass)
    class SingletonDataClass:
        value: int

    instance1 = SingletonDataClass(10)
    instance2 = SingletonDataClass(20)
    assert instance1 is instance2

    if allow_reassignment:
        assert instance1.value == 20
    else:
        assert instance1.value == 10


@pytest.mark.parametrize(
    ("thread_safe", "allow_subclass", "allow_reassignment"),
    list(product((True, False), repeat=3)),
)
def test_singleton_with_function(
    thread_safe: bool,
    allow_subclass: bool,
    allow_reassignment: bool,
):
    with pytest.raises(
        TypeError,
        match="singleton decorator can only be applied to classes",
    ):

        @singleton(
            thread_safe=thread_safe,
            allow_subclass=allow_subclass,
            allow_reassignment=allow_reassignment,
        )  # type: ignore
        def some_function():
            pass


def test_singleton_with_function_and_without_arguments():
    with pytest.raises(
        TypeError,
        match="singleton decorator can only be applied to classes",
    ):

        @singleton  # type: ignore
        def some_function():
            pass


def test_subclass_not_singleton():
    @singleton(allow_subclass=True)
    class ParentSingleton:
        pass

    class Child(ParentSingleton):
        pass

    with pytest.raises(
        TypeError,
        match=f"Subclass {Child.__name__} must also be a singleton",
    ):
        Child()


def test_instances_do_not_conflict():
    @singleton
    class SingletonA:
        pass

    @singleton
    class SingletonB:
        pass

    instance_a1 = SingletonA()
    instance_a2 = SingletonA()
    instance_b1 = SingletonB()
    instance_b2 = SingletonB()

    assert instance_a1 is instance_a2
    assert instance_b1 is instance_b2
    assert instance_a1 is not instance_b1
    assert isinstance(instance_a1, SingletonA)
    assert isinstance(instance_b1, SingletonB)


def test_instances_do_not_conflict_with_parent():
    @singleton(allow_subclass=True)
    class Parent:
        pass

    @singleton
    class Child(Parent):
        pass

    instance_a1 = Parent()
    instance_a2 = Parent()
    instance_b1 = Child()
    instance_b2 = Child()

    assert instance_a1 is instance_a2
    assert instance_b1 is instance_b2
    assert instance_a1 is not instance_b1
    assert isinstance(instance_a1, Parent)
    assert isinstance(instance_b1, Child)


def test_singleton_flag():
    @singleton(allow_subclass=True)
    class Singleton:
        pass

    @singleton
    class Subclass(Singleton):
        pass

    class NonSingletonSubclass(Singleton):
        pass

    assert getattr(Singleton, _SINGLETON_FLAG) == Singleton.__name__
    assert getattr(Subclass, _SINGLETON_FLAG) == Subclass.__name__
    assert getattr(NonSingletonSubclass, _SINGLETON_FLAG) == Singleton.__name__


def test_is_singleton():
    assert not is_singleton(1)

    class NonSingleton:
        pass

    assert not is_singleton(NonSingleton)

    @singleton(allow_subclass=True)
    class Singleton:
        pass

    assert is_singleton(Singleton)

    @singleton
    class Subclass(Singleton):
        pass

    assert is_singleton(Subclass)

    class NonSingletonSubclass(Singleton):
        pass

    assert not is_singleton(NonSingletonSubclass)
