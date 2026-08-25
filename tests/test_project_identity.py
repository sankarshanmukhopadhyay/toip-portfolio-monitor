import unittest

import trust_ecosystem_monitor
import toip_monitor
from trust_ecosystem_monitor.cli import main
from trust_ecosystem_monitor.profile import load_profile


class ProjectIdentityTests(unittest.TestCase):
    def test_canonical_package_identity(self):
        self.assertEqual(trust_ecosystem_monitor.__version__, toip_monitor.__version__)

    def test_default_profile_remains_trustoverip(self):
        profile = load_profile()
        self.assertEqual(profile.organization, "trustoverip")

    def test_canonical_cli_is_importable(self):
        self.assertTrue(callable(main))


if __name__ == "__main__":
    unittest.main()
