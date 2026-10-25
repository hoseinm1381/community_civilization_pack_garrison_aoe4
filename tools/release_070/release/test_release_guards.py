"""Release contract tests; no native editor, Blender or archive mutation."""
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace

import common as c
import assemble_release as assembly
import package_release as package
from verify_release import compare_members


class ReleaseGuards(unittest.TestCase):
    def test_unpack_plain_output_is_not_parsed_as_json(self):
        with patch.object(c.subprocess,"run",return_value=SimpleNamespace(returncode=0,stdout="",stderr="")):
            self.assertEqual(c.command("unpack","unused")["returncode"],0)
        with patch.object(c.subprocess,"run",return_value=SimpleNamespace(returncode=1,stdout="",stderr="unpack failed")):
            with self.assertRaisesRegex(RuntimeError,"unpack failed"): c.command("unpack","unused")

    def fixture(self):
        rows = []
        for family in sorted(c.EXPECTED_FAMILIES - {"monk_precache"}):
            for member in (f"attrib/ebps/{family}.rgd", f"art/{family}.rrgeom"):
                rows.append(dict(member=member, family=family, file="unused", sha256="b"*64, bytes=3))
        rows.append(dict(member=c.MONK_MEMBER, family="monk_precache", file="unused", sha256="b"*64, bytes=3))
        rows.sort(key=lambda row: row["member"])
        return dict(schema="ccp-070-qualified-integration-allowlist/v1",
                    status="static_payloads_qualified_final_archive_not_built",
                    baseline_sga_sha256="baseline", monk_candidate_sga_sha256="monk",
                    payloads=rows, changed_resource_allowlist=[r["member"] for r in rows],
                    scoped_compiled_actor_members=[r["member"] for r in rows if r["member"].startswith("attrib/")])

    def validate(self, receipt):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/"payload"; path.write_bytes(b"new")
            with patch.object(c, "owned_file", return_value=path), patch.object(c, "sha", return_value="b"*64):
                return c.validate_allowlist(receipt, {"baseline_sga_sha256":"baseline"},
                                           {"candidate_sha256":"monk", "member_hashes_before":{}})

    def test_complete_allowlist(self):
        self.assertEqual(len(self.validate(self.fixture())), 9)

    def test_incomplete_receipt_rejected(self):
        receipt=self.fixture(); receipt["status"]="in_progress"
        with self.assertRaisesRegex(ValueError,"qualified"): self.validate(receipt)

    def test_missing_family_actor_rejected(self):
        receipt=self.fixture()
        for row in receipt["payloads"]:
            if row["member"]=="attrib/ebps/garden.rgd": row["family"]="foundry"
        with self.assertRaisesRegex(ValueError,"actor and art"): self.validate(receipt)

    def test_unlisted_payload_rejected(self):
        receipt=self.fixture(); receipt["changed_resource_allowlist"].pop()
        with self.assertRaisesRegex(ValueError,"exact"): self.validate(receipt)

    def test_only_private_070_attachment_lists_permitted(self):
        receipt=self.fixture()
        row=dict(member="attrib/attachments/attachment_lists/vietnam/release_070/a.rgd",
                 family="garden",file="unused",sha256="b"*64,bytes=3)
        receipt["payloads"].append(row)
        receipt["payloads"].sort(key=lambda r:r["member"])
        receipt["changed_resource_allowlist"]=sorted(r["member"] for r in receipt["payloads"])
        self.assertEqual(len(self.validate(receipt)),10)
        row["member"]="attrib/attachments/attachment_lists/chinese/a.rgd"
        receipt["payloads"].sort(key=lambda r:r["member"])
        receipt["changed_resource_allowlist"]=sorted(r["member"] for r in receipt["payloads"])
        with self.assertRaisesRegex(ValueError,"scope"): self.validate(receipt)

    def test_unsafe_paths(self):
        for name in ("../art/a", "art/../a", "art/./a", "art//a", "art/a/", "art\\a", "/art/a"):
            with self.subTest(name=name), self.assertRaises(ValueError): c.member_kind(name)

    def test_foreign_payload_root_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"a"; path.write_bytes(b"x")
            with self.assertRaisesRegex(ValueError,"outside"): c.owned_file(path)

    def test_normal_external_drift_requires_exact_pinned_inventory(self):
        before={".aoe4/Vietnam_v2/Layout.xml":{"sha256":"old","bytes":1},
                "archives/Vietnam_v2.sga":{"sha256":"old","bytes":1}}
        observed={k:{"sha256":"new","bytes":2} for k in before}
        added="assets/attrib/instances/ai/ai_economy/complete/default_economy.xml"
        observed[added]={"sha256":"add","bytes":3}
        receipt=dict(schema="ccp-070-external-normal-drift/v1",freeze_sha256="freeze",
                     normal_root=c.CFG["source_root"],normal_observed_inventory=observed,
                     observed_file_count=3,frozen_unchanged_file_count=0,
                     differences={k:{"frozen":before.get(k),"observed":v} for k,v in observed.items()},
                     changed_paths=sorted(list(before)+[added]),
                     normal_frozen_preservation_passed=False)
        with patch.object(c,"inventory",return_value=observed),patch.object(Path,"is_file",return_value=True),\
             patch.object(c,"read",return_value=receipt),patch.object(c,"sha",return_value="freeze"):
            result=c.verify_normal({"normal":before})
            self.assertFalse(result["normal_frozen_preservation_passed"])
            self.assertTrue(result["normal_observed_drift_inventory_preserved"])
            receipt["normal_observed_inventory"]={}
            with self.assertRaisesRegex(ValueError,"explicit observed"): c.verify_normal({"normal":before})

    def test_mounts_identity_and_collision(self):
        listing={"members":[{"path":"art/a", "toc":"data"}],
                 "archive":{"name":c.CFG["project_guid"],"verification":{"verified":True}}}
        self.assertEqual(c.validate_mounts(listing),{"art/a":"data"})
        for mutation in ("mount", "identity", "crc", "collision"):
            value=copy.deepcopy(listing)
            if mutation=="mount": value["members"][0]["toc"]="attrib"
            if mutation=="identity": value["archive"]["name"]="wrong"
            if mutation=="crc": value["archive"]["verification"]["verified"]=False
            if mutation=="collision": value["members"].append({"path":"art/A","toc":"data"})
            with self.subTest(mutation=mutation), self.assertRaises(ValueError): c.validate_mounts(value)

    def test_full_byte_delta_refuses_unlisted_change(self):
        with self.assertRaisesRegex(ValueError,"allowlist"):
            compare_members({"art/a":{"sha256":"old","bytes":3}}, {"art/a":{"sha256":"new","bytes":3}}, {})

    def test_incomplete_family_evidence(self):
        with self.assertRaisesRegex(ValueError,"Missing qualified"):
            assembly.verify_evidence({"per_family_evidence":{"garden":{}}})

    def test_strict_version_and_native_gates(self):
        manifest={"schema":"garrison.mod/v1","bundle_key":c.KEY,
                  "details":{"id":c.KEY,"version":c.VERSION,"author":c.CREDITS,"content_types":["game-mode","tuning-pack"]},
                  "members":[{"mod_key":c.KEY,"role":"tuning","path":c.KEY+".sga","sha256":"hash"}]}
        package.check_manifest(manifest,"hash")
        for version in ("0.7.0-test", "0.7.0.1", "0.6.1"):
            manifest["details"]["version"]=version
            with self.assertRaises(ValueError): package.check_manifest(manifest,"hash")
        evidence=dict(schema="ccp.release070.evidence/v1",version=c.VERSION,is_final_release=True,
                      credits=c.CREDITS,sga_sha256="hash",baseline061_sga_sha256="base",gates=dict(package.GATES))
        package.check_evidence(evidence,"hash","base")
        evidence["gates"]["native_gameplay"]=True
        with self.assertRaises(ValueError): package.check_evidence(evidence,"hash","base")

if __name__ == "__main__": unittest.main()
