import unittest

from plan import contracts, check, load, selftest


class RegistryAndPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry, cls.assumptions, cls.roadmap, cls.docs = load()
        cls.capabilities = cls.registry["capabilities"]
        cls.ids = {item["id"] for item in cls.capabilities}

    def test_registry_ids_are_unique(self):
        self.assertEqual(len(self.ids), len(self.capabilities))

    def test_registry_dependencies_resolve(self):
        missing = [
            (item["id"], dep)
            for item in self.capabilities
            for dep in item.get("depends_on", [])
            if dep not in self.ids
        ]
        self.assertEqual(missing, [])

    def test_checked_capabilities_have_strong_evidence(self):
        strong = {"PROVEN", "SUPPORTED"}
        invalid = [
            item["id"]
            for item in self.capabilities
            if item.get("checked")
            and not any(ev.get("grade") in strong for ev in item.get("evidence", []))
        ]
        self.assertEqual(invalid, [])

    def test_plan_rules_have_no_failures(self):
        failures, _warnings = check(
            self.registry, self.assumptions, self.roadmap, self.docs
        )
        self.assertEqual(failures, [])

    def test_plan_mutations_are_detected(self):
        outcomes = selftest(self.registry, self.assumptions, self.roadmap, self.docs)
        self.assertTrue(outcomes, "the plan self-test must contain mutation cases")
        self.assertTrue(all(result[2] for result in outcomes), outcomes)

    def test_scenario_contracts_hold(self):
        outcomes = contracts(self.assumptions, self.roadmap)
        self.assertTrue(outcomes, "the plan must declare scenario contracts")
        self.assertTrue(all(ok for _description, ok in outcomes), outcomes)


if __name__ == "__main__":
    unittest.main()
