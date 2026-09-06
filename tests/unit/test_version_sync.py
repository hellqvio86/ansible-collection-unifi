from scripts.check_version_sync import main


def test_readme_version_matches_galaxy():
    assert main() == 0
