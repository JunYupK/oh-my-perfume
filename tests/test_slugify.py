from crawler.worker import _slugify


def test_slugify_replaces_spaces_and_slashes():
    assert _slugify(" Jo-Malone-London ") == "jo-malone-london"
    assert _slugify("Giorgio/Armani") == "giorgio-armani"
