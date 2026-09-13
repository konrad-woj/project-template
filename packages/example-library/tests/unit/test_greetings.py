from example_library import build_greeting


def test_build_greeting_includes_name() -> None:
    assert build_greeting("World") == "Hello, World!"
