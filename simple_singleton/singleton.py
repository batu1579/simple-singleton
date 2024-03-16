from functools import wraps
from threading import Lock
from types import MethodType
from typing import Any, Callable, Optional, Type, TypeVar, Union, cast, overload

_T = TypeVar("_T")
_SINGLETON_FLAG = "__singleton_flag__"


@overload
def singleton(_cls: Type[_T]) -> Type[_T]: ...  # pragma: no cover


@overload
def singleton(
    *,
    thread_safe: bool = False,
    allow_subclass: bool = False,
    allow_reassignment: bool = False,
) -> Callable[[Type[_T]], Type[_T]]: ...  # pragma: no cover


def singleton(
    _cls: Optional[Type[_T]] = None,
    *,
    thread_safe: bool = False,
    allow_subclass: bool = False,
    allow_reassignment: bool = False,
) -> Union[Callable[[Type[_T]], Type[_T]], Type[_T]]:
    """A decorator to enforce the singleton pattern on a class.

    Usage:
    ::

        @singleton
        class SingletonClass:
            ...

    Even if you create multiple objects, all will reference the same instance.
    ::

        instance1 = SingletonClass()
        instance2 = SingletonClass()
        assert id(instance1) == id(instance2)  # True

    Thread-safe:

    In a multi-threaded environment, use 'thread_safe=True' to enable
    double-checked locking. This ensures thread-safe instance creation while
    maintaining performance.
    ::

        @singleton(thread_safe=True)
        class ThreadSafeSingleton:
            ...

    Allow Subclassing:

    Set 'allow_subclass=True' to enable subclassing the singleton class.
    ::

        @singleton(allow_subclass=True)  # Allows subclassing
        class SubclassableSingleton:
            ...

        @singleton
        class Subclass(SubclassableSingleton):
            ...

    Without this option, attempting to subclass a singleton will raise a TypeError.
    ::

        @singleton  # Defaults to don't allows subclassing
        class UnsubclassableSingleton:
            ...

        @singleton
        class Subclass(UnsubclassableSingleton):
            ...

        Subclass()  # Raise TypeError when instance

    Each subclass must also be a singleton, otherwise, a TypeError is raised.
    ::

        class Subclass(SubclassableSingleton):
            ...

        Subclass()  # Raises TypeError when instance

    Allow Reassignment:

    Use 'allow_reassignment=True' to allow reinitializing the singleton instance.
    The instance will be the same, but `__init__` will be called again with new
    arguments.
    ::

        @singleton(allow_reassignment=True)  # Allows reinitialization
        class ReassignableSingleton:
            def __init__(self, value) -> None:
                self.value = value

        instance1 = ReassignableSingleton("initial")
        print(instance1.value)  # Output: initial

        instance2 = ReassignableSingleton("reassigned")
        print(instance1.value)  # Output: reassigned
        print(instance2.value)  # Output: reassigned

    The instance remains the same, but its state can be changed via reassignment.
    ::

        instance1 = ReassignableSingleton("initial")
        instance1_id = id(instance1)

        instance2 = ReassignableSingleton("reassigned")
        instance2_id = id(instance2)

        assert instance1_id == instance2_id  # True

    Args:
        thread_safe (bool, optional): Enables thread safety during instance
            creation. Defaults to False.
        allow_subclass (bool, optional): Allows subclassing of the singleton
            class. Defaults to False.
        allow_reassignment (bool, optional): Allows reinitialization of the
            singleton instance. Defaults to False.

    Returns:
        Callable[[Type[_T]], Type[_T]]: When called with parameters: Returns
            a decorator function that, when applied, transforms the decorated
            class into a singleton.
        Type[_T]: When called without parameters: Directly applies the returned
            decorator to the decorated class, enforcing its singleton nature.

    Notes:

    This implementation overrides the class's __new__ and __init__ methods.
    Whether the original class's __init__ method is overridden depends on the
    allow_reassignment flag. If this flag is set to true, __init__ will be
    overridden; otherwise, it won't be.

    After using the singleton decorator, a class attribute named __singleton_flag__
    is added to the original class, which holds the name of the last class
    in the inheritance chain that used the singleton decorator. If the class
    itself has applied the decorator, this value will be its own class name.
    This attribute is used to ensure that subclasses are correctly set up,
    and typically, this value should always match the class name. When using
    this decorator, avoid using the identifier __singleton_flag__ in your classes.

    Subclass checking is implemented using assertions, making it easy to disable
    them in production environments to enhance performance. However, it's
    advised not to disable these assertions during development as they help
    prevent logical errors, such as a singleton subclass not being unique.
    Do not use exceptions raised by this decorator for purposes other than
    intended, as exceptions related to subclass checks will not be thrown once
    subclass checking is disabled.
    """

    def decorator(original_cls: Type[_T]) -> Type[_T]:
        _lock: Lock = Lock()
        _instance: Optional[_T] = None
        _is_initialized: bool = False
        _original_new: Callable[..., _T] = original_cls.__new__
        _original_init: Callable[..., None] = original_cls.__init__

        def _check_subclass(cls: Type[_T]) -> bool:
            if not allow_subclass:
                raise TypeError(
                    f"Singleton class {original_cls.__name__} cannot be inherited",
                )

            if getattr(cls, _SINGLETON_FLAG, None) != cls.__name__:
                # Not using singleton decorator
                raise TypeError(
                    f"Subclass {cls.__name__} must also be a singleton",
                )

            return True

        def _create_instance(cls: Type[_T], *args: Any, **kwargs: Any) -> _T:
            # Create instance by original init method
            if _original_new is object.__new__:
                return _original_new(cls)
            return _original_new(cls, *args, **kwargs)

        @wraps(original_cls.__new__)
        def __new__(cls: Type[_T], *args: Any, **kwargs: Any) -> _T:
            nonlocal _instance
            cls = args[0]

            if cls is not original_cls:
                # if cls is a subclass of original_cls
                _check_subclass(cls)
                _instance = _create_instance(cls, *args, **kwargs)
                return _instance

            if _instance is None:
                if thread_safe:
                    with _lock:
                        # Double-checked locking to avoid duplicate creation
                        if _instance is None:
                            _instance = _create_instance(cls, *args, **kwargs)
                        else:
                            pass  # For test coverage
                else:
                    _instance = _create_instance(cls, *args, **kwargs)
            return _instance

        @wraps(original_cls.__init__)
        def __init__(self: _T, *args: Any, **kwargs: Any) -> None:
            nonlocal _is_initialized

            if not _is_initialized:
                _original_init(self, *args, **kwargs)
                _is_initialized = True

        if not isinstance(original_cls, type):
            raise TypeError(
                "singleton decorator can only be applied to classes",
            )

        if not allow_reassignment:
            original_cls.__init__ = __init__
        original_cls.__new__ = MethodType(__new__, original_cls)
        setattr(original_cls, _SINGLETON_FLAG, original_cls.__name__)

        return cast(Type[_T], original_cls)

    # If called as a decorator with no arguments
    if _cls is not None:
        return decorator(_cls)

    return decorator


def is_singleton(cls: Any) -> bool:
    """Check if a class is a singleton.

    Args:
        cls (Any): The class to check.

    Returns:
        bool: The following cases return false, otherwise true:

        - The target object is not a class.
        - The class has not been decorated with the singleton decorator.
        - The parent class is a singleton, but the class itself is not
    """
    # Check whether the target object a class
    if not isinstance(cls, type):
        return False

    flag = getattr(cls, _SINGLETON_FLAG, None)

    # Check whether the class has flag
    if flag is None:
        return False

    # Check whether flag is equal to the name of the class itself
    return flag == cls.__name__
