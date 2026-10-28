import json
import unittest
from pathlib import Path
from build_spec import build
from check_spec import check, selftest
ROOT=Path(__file__).resolve().parents[1]
class SystemSpecTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / "system.json").open("r",encoding="utf-8") as handle: cls.spec=json.load(handle)
        with (ROOT / "registry.json").open("r",encoding="utf-8") as handle: cls.registry=json.load(handle)
    def test_spec_passes_all_rules(self): self.assertEqual(check(self.spec,self.registry),[])
    def test_default_and_conversion_policy_are_fail_closed(self):
        self.assertEqual(self.spec["default_authorization"],"DENY")
        self.assertEqual(next(p for p in self.spec["policies"] if p["id"]=="P-CAPI-DISPATCH")["state"],"DENY")
    def test_generator_matches_committed_system_json(self): self.assertEqual(build(),self.spec)
    def test_all_spec_mutants_are_detected(self):
        results=selftest(self.spec,self.registry)
        self.assertTrue(results); self.assertTrue(all(item[2] for item in results),results)
if __name__ == "__main__": unittest.main()
