from ament_copyright.main import main
import pytest


# Remove the skip once every project source file has a copyright header.
@pytest.mark.skip(reason='Project source files do not carry per-file copyright headers.')
@pytest.mark.copyright
@pytest.mark.linter
def test_copyright():
    """Check project source files for copyright notices."""
    rc = main(argv=['.', 'test'])
    assert rc == 0, 'Found errors'
