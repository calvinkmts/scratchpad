def decorator(cls):
    cls.a = 42
    return cls

@decorator
class C:
    pass

assert hasattr(C, "a")

