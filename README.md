# simple-singleton

A simple Python library to conveniently convert classes into singleton classes.

## Features

- Easy-to-use singleton decorator
- Thread-safe singleton initialization
- Support for subclassing and reassignment
- 100% test coverage

## Installation

Install the library directly from the GitHub repository using pip:

```bash
pip install git+https://github.com/batu1579/simple-singleton
```

## Usage

To use the singleton decorator, simply import it from the `simple_singleton` package and apply it to your class:

```python
from simple_singleton import singleton

@singleton
class SingletonClass:
    ...

instance1 = SingletonClass()
instance2 = SingletonClass()
assert id(instance1) == id(instance2)  # True
```

If no parameters are used, the effect of the decorator is equivalent to using the following parameters:

```python
@singleton(
    thread_safe=False,
    allow_subclass=False,
    allow_reassignment=False,
)
class SingletonClass:
    ...
```

### Thread-safe:

In a multi-threaded environment, use 'thread_safe=True' to enable double-checked locking. This ensures thread-safe instance creation while maintaining performance.

```python
@singleton(thread_safe=True)
class ThreadSafeSingleton:
    ...
```

### Allow Subclassing:

Set `allow_subclass=True` to enable subclassing the singleton class.

```python
@singleton(allow_subclass=True)
class SubclassableSingleton:
    ...

@singleton
class Subclass(SubclassableSingleton):
    ...
```

Without this option, attempting to subclass a singleton will raise a TypeError.

```python
@singleton(allow_subclass=False)
class UnsubclassableSingleton:
    ...

@singleton
class Subclass(UnsubclassableSingleton):
    ...

Subclass()  # Raise TypeError when instance
```

Each subclass must also be a singleton, otherwise, a TypeError is raised.

```python
class Subclass(SubclassableSingleton):
    ...

Subclass()  # Raises TypeError when instance
```

### Allow Reassignment:

Use `allow_reassignment=True` to allow reinitializing the singleton instance. The instance will be the same, but `__init__` will be called again with new arguments.

```python
@singleton(allow_reassignment=True)
class ReassignableSingleton:
    def __init__(self, value) -> None:
        self.value = value

instance1 = ReassignableSingleton("initial")
print(instance1.value)  # Output: initial

instance2 = ReassignableSingleton("reassigned")
print(instance1.value)  # Output: reassigned
print(instance2.value)  # Output: reassigned
```

The instance remains the same, but its state can be changed via reassignment.

```python
instance1 = ReassignableSingleton("initial")
instance1_id = id(instance1)

instance2 = ReassignableSingleton("reassigned")
instance2_id = id(instance2)

assert instance1_id == instance2_id  # True
```

### Check Is Singleton

The library provides a function to check whether a class has been correctly converted to a singleton class.

```python
from simple_singleton import is_singleton, singleton

@singleton(allow_subclass=True)
class Singleton:
    ...

@singleton
class Subclass:
    ...

class NonSingletonSubclass(Singleton):
    ...

assert is_singleton(Singleton)
assert is_singleton(Subclass)
assert not is_singleton(NonSingletonSubclass)
```

## Notes

1. This implementation overrides the class's `__new__` and `__init__` methods. Whether the original class's `__init__` method is overridden depends on the allow_reassignment flag. If this flag is set to true, `__init__` will be overridden; otherwise, it won't be.
2. After using the singleton decorator, a class attribute named `"__singleton_flag__"` is added to the original class, which holds the name of the last class in the inheritance chain that used the singleton decorator. If the class itself has applied the decorator, this value will be its own class name. This attribute is used to ensure that subclasses are correctly set up, and typically, this value should always match the class name. When using this decorator, avoid using the identifier `"__singleton_flag__"` in your classes.
3. Subclass checking is implemented using assertions, making it easy to disable them in production environments to enhance performance. However, it's advised not to disable these assertions during development as they help prevent logical errors, such as a singleton subclass not being unique. Do not use exceptions raised by this decorator for purposes other than intended, as exceptions related to subclass checks will not be thrown once subclass checking is disabled.

## Contributing

Welcome to submit PR, issue and feature requests!

To contribute to this project, clone the repository and install the development dependencies:

```bash
# Clone this repository
git clone https://github.com/batu1579/simple-singleton

# Enter the repository folder
cd simple-singleton

# Install all developmetn dependencies
pip install -e .[dev]
```

Please use run all test case before you submit your PR:

```bash
python -m pytest
```

Ensure that all test cases pass and that the coverage is 100%. If the coverage is less than 100%, write the corresponding test case

## Changelog

See [CHANGELOG](./CHANGELOG.md)

## License

This project is licensed under the Mozilla Public License 2.0 (MPL 2.0). See the [LICENSE](./LICENSE) file for details.