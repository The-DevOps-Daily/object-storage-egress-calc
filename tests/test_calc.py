import unittest

from calc import price, tiered

BASE = {"storage_gb": 1000, "egress_gb": 2000, "gets": 0, "puts": 0, "lifetime_days": 365}


def scenario(**kw):
    return {**BASE, **kw}


class TieredTest(unittest.TestCase):
    def test_tiers_add_up(self):
        tiers = [[100, 1.0], [None, 0.5]]
        self.assertEqual(tiered(50, tiers), 50)
        self.assertEqual(tiered(300, tiers), 100 + 200 * 0.5)


class PriceTest(unittest.TestCase):
    def test_free_allowance_then_paid_egress(self):
        p = {"storage_tiers": [[None, 0.02]], "egress": {"free_gb": 100, "tiers": [[None, 0.09]]}}
        cost, notes = price(p, scenario())
        self.assertAlmostEqual(cost, 1000 * 0.02 + 1900 * 0.09)
        self.assertEqual(notes, [])

    def test_free_egress_ratio_of_storage(self):
        p = {"storage_tiers": [[None, 0.006]], "egress": {"free_ratio_of_storage": 3, "tiers": [[None, 0.01]]}}
        cost, _ = price(p, scenario(egress_gb=5000))
        self.assertAlmostEqual(cost, 1000 * 0.006 + 2000 * 0.01)

    def test_fair_use_policy_is_a_note_not_a_price(self):
        p = {"storage_tiers": [[None, 0.007]],
             "egress": {"tiers": [[None, 0.0]], "policy_max_ratio_of_storage": 1, "policy_note": "outside policy"}}
        cost, notes = price(p, scenario())
        self.assertAlmostEqual(cost, 7.0)
        self.assertEqual(notes, ["outside policy"])

    def test_bundle(self):
        p = {"bundle": {"price": 5, "storage_gb": 250, "egress_gb": 1024,
                        "extra_storage_per_gb": 0.02, "extra_egress_per_gb": 0.01}}
        cost, _ = price(p, scenario())
        self.assertAlmostEqual(cost, 5 + 750 * 0.02 + 976 * 0.01)

    def test_minimum_storage_duration(self):
        p = {"storage_tiers": [[None, 0.01]], "egress": {"tiers": [[None, 0.0]]}, "min_storage_days": 90}
        cost, notes = price(p, scenario(lifetime_days=30))
        self.assertAlmostEqual(cost, 1000 * 3 * 0.01)
        self.assertTrue(notes)

    def test_requests_and_minimum_monthly(self):
        p = {"storage_tiers": [[None, 0.01]], "egress": {"tiers": [[None, 0.0]]},
             "requests": {"class_b_per_1000": 0.0004, "free_class_b": 1000}, "minimum_monthly": 20}
        cost, notes = price(p, scenario(storage_gb=10, gets=2000))
        self.assertEqual(cost, 20)
        self.assertIn("minimum monthly charge $20", notes)


if __name__ == "__main__":
    unittest.main()
