import unittest


class StageThreeGateProbe(unittest.TestCase):
    def test_required_checks_block_a_known_failure(self):
        self.fail("intentional ticket 064 quality-gate probe")


if __name__ == "__main__":
    unittest.main()
