"""Offline regression controls for the reusable private geometry route."""
from __future__ import annotations

import copy
import unittest
from pathlib import Path

import authored_geometry_060 as route
from ranged_media_pairs_060 import qualify_pair, variant_rgm_stock_except_path
from common import EXPORT, OUT, read, sha
from geometry_continuation_batch_060 import build_spec, corrected_73_spec
from worker_tug_native_060 import source_contract as tug_source_contract, worker_rig_text, worker_structure


class AuthoredGeometryTests(unittest.TestCase):
    def test_real_villager_fbx_has_three_skin_bindings(self):
        path = EXPORT / "villager-geometry-route/male/stock-three-lod-control/model.fbx"
        skin, cluster = route.fbx_skin_counts(path)
        self.assertEqual(skin, 3)
        self.assertGreater(cluster, 3)

    def test_unskinned_fbx_refused(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as folder:
            file = Path(folder) / "empty.fbx"
            file.write_bytes(b"Kaydara FBX Binary  \x00\x1a\x00")
            with self.assertRaisesRegex(RuntimeError, "skin and cluster"):
                route.fbx_skin_counts(file)

    def test_existing_48_and_73_bone_controls(self):
        archer = read(OUT / "qualification/archer-pairing-prep/manual-uvfix/three-lod-comparison.json")
        stock = read(Path(archer["stock_manifest"]))
        cooked = read(Path(archer["compiled_manifest"]))
        self.assertEqual(route.rig_contract(cooked, stock, 48)["palette_bones"], 46)
        self.assertTrue(all(x["passed"] for x in archer["three_lods"]))
        villager = read(OUT / "qualification/villager-geometry-route/contract-v2.json")["genders"]["male"]
        decoded = read(OUT / "qualification/villager-geometry-route/20261018-resume/male/manual/decode-local.json")
        stock = read(Path(villager["donor_manifest"]))
        cooked = read(Path(decoded["decoded_manifest"]))
        # The villager qualification admits only the measured, unskinned
        # pelvis socket leaf; active skin/bind records stay inside tolerance.
        result = route.rig_contract(cooked, stock, 73)
        self.assertEqual(result["nondeforming_leaf_exception"]["bone"], "metarig_pelvissocket")
        self.assertLess(result["max_transform_scalar_deltas"]["inverse_bind"], .0002)
        tampered = copy.deepcopy(cooked)
        socket = next(x for x in tampered["skeleton"]["bones"] if x["name"] == "metarig_pelvissocket")
        socket["name"] = "metarig_other"
        with self.assertRaisesRegex(RuntimeError, "hierarchy differs"):
            route.rig_contract(tampered, stock, 73)

    def test_villager_exception_rejects_skinned_or_child_socket(self):
        row = read(OUT / "qualification/villager-geometry-route/contract-v2.json")["genders"]["female"]
        decoded = read(OUT / "qualification/villager-geometry-route/20261018-resume/female/manual/decode-local.json")
        stock, cooked = read(Path(row["donor_manifest"])), read(Path(decoded["decoded_manifest"]))
        self.assertIsNotNone(route.rig_contract(cooked, stock, 73)["nondeforming_leaf_exception"])
        skinned = copy.deepcopy(cooked)
        socket = next(x for x in skinned["skeleton"]["bones"] if x["name"] == "metarig_pelvissocket")
        skinned["skeleton"]["skin_palettes"][0]["bones"][0]["skeleton_index"] = socket["index"]
        with self.assertRaises(RuntimeError): route.rig_contract(skinned, stock, 73)
        child = copy.deepcopy(cooked)
        child["skeleton"]["bones"][1]["parent_index"] = socket["index"]
        with self.assertRaises(RuntimeError): route.rig_contract(child, stock, 73)

    def test_female_age3_exact_native_58_bone_palette(self):
        path = EXPORT / "civilian_roster/chi_villager_female_age03/v3/authored-snapshot.json"
        source = read(path)
        stock = read(Path(source["source_manifest"]))
        spec = {"skeleton_bones": 73, "group_name": source["geometry"]["groups"][0]["name"]}
        self.assertEqual(route.rig_contract(source, stock, 73)["palette_bones"], 58)
        self.assertEqual(len(route.source_contract(spec, source, stock)), 3)

    def test_remaining_exact_donor_palettes_45_and_56(self):
        for slug, count in (("maa3", 45), ("monk4", 56)):
            folder = EXPORT / "remaining_roster" / slug / ("v2" if slug == "monk4" else "v1")
            source = read(folder / "authored-snapshot.json")
            stock = read(Path(source["source_manifest"]))
            bones = len(stock["skeleton"]["bones"])
            spec = {"skeleton_bones": bones, "group_name": source["geometry"]["groups"][0]["name"]}
            self.assertEqual(route.rig_contract(source, stock, bones)["palette_bones"], count)
            self.assertEqual(len(route.source_contract(spec, source, stock)), 3)

    def test_remaining_geometry_spec_pins_exact_donor_and_export(self):
        spec = build_spec("maa3", "m13g")
        self.assertEqual(spec["skeleton_bones"], 48)
        self.assertEqual(spec["group_name"], "mon_infantry_armor_age03")
        self.assertEqual(spec["stock_manifest_sha256"], sha(spec["stock_manifest"]))
        self.assertEqual(route.fbx_skin_counts(Path(spec["fbx"])), (3, 144))

    def test_source_preflight_rejects_nonunit_corner_normal(self):
        path = OUT / "authored-geometry/archer4-v5b/spec.json"
        spec = read(path)
        source = read(Path(spec["authored_snapshot"]))
        stock = read(Path(spec["stock_manifest"]))
        with self.assertRaisesRegex(RuntimeError, "non-unit corner normal"):
            route.source_contract(spec, source, stock)

    def test_prepared_rig_must_match_exact_donor_bone_order(self):
        spec = read(OUT / "authored-geometry/villager-female1-v2/spec.json")
        donor = read(Path(spec["stock_manifest"]))
        wrong = Path(spec["template_body"]) / "model.rig"
        with self.assertRaisesRegex(RuntimeError, "rig bones"):
            route.rig_file_contract(wrong, donor)
        correct = Path("staging/release_060/vf/Mods/v60f/project/source/art/scenario/garrison/"
                       "v60f/units/v60f_villager_geometry_control/body/model.rig")
        self.assertEqual(route.rig_file_contract(correct, donor), 73)

    def test_corrected_73_spec_uses_exact_villager_rig_template(self):
        spec = corrected_73_spec("villager-female1-v2")
        donor = read(Path(spec["stock_manifest"]))
        self.assertEqual(route.rig_file_contract(Path(spec["template_body"]) / "model.rig", donor), 73)
        self.assertEqual(spec["slug"], "villager-female1-v2-r73")

    def test_worker_tug_v8_exact_24_group_source_contract(self):
        result = tug_source_contract()
        self.assertEqual(result["group_count"], 24)
        self.assertEqual(result["palette_bones"], [2, 2, 2, 2, 2, 52, 2, 2])
        self.assertEqual(result["changed_group_indices"], [0, 1, 2])

    def test_worker_tug_diagnostic_rig_pins_exact_140_bones(self):
        result = tug_source_contract()
        donor = read(Path(result["donor"]))
        text = worker_rig_text(donor)
        self.assertEqual(text.splitlines().count("[BONES START]"), 1)
        self.assertIn("fullbody_lod3 tsmg_root", text)
        self.assertEqual(len(text.split("[BONES START]\n", 1)[1].split("\n[END]", 1)[0].splitlines()), 140)

    def test_worker_native_group_and_palette_gate_refuses_merged_readback(self):
        source = read(Path(tug_source_contract()["snapshot"]))
        receipt = read(OUT / "authored-geometry/tug-worker-v8/readback.json")
        cooked = read(Path(receipt["decoded_manifest"]))
        self.assertTrue(worker_structure(source, source)["passed"])
        result = worker_structure(source, cooked)
        self.assertFalse(result["passed"])
        self.assertEqual(result["source_groups"], 24)
        self.assertEqual(result["compiled_groups"], 18)
        self.assertEqual(result["source_palette_bones"], [2, 2, 2, 2, 2, 52, 2, 2])
        self.assertEqual(result["compiled_palette_bones"], [52])

    def test_archer4_v5c_only_repairs_four_lod2_source_normals(self):
        old = read(EXPORT / "ranged_roster/archer4/v5b/authored-snapshot.json")
        new = read(EXPORT / "ranged_roster/archer4/v5c/authored-snapshot.json")
        self.assertEqual(route.corrected_ranged_normal_count(old, new), 4)

    def test_civilian_export_receipt_pins_nested_file_hashes(self):
        folder = EXPORT / "civilian_roster/chi_villager_male_age01/v2"
        source = read(folder / "authored-snapshot.json")
        spec = {"fbx": str(folder / "model.fbx"), "action": str(folder / "action.json"),
                "albedo": str(folder / "albedo.png"),
                "authored_snapshot": str(folder / "authored-snapshot.json"),
                "export_receipt": str(OUT / "qualification/civilian_roster/chi_villager_male_age01/v2/export.json"),
                "stock_manifest": source["source_manifest"],
                "stock_manifest_sha256": sha(source["source_manifest"]),
                "skeleton_bones": 73}
        self.assertEqual(route.source_inputs(spec)[0], folder / "model.fbx")

    def test_authored_shape_is_comparison_basis(self):
        archer = read(OUT / "qualification/archer-pairing-prep/manual-uvfix/three-lod-comparison.json")
        source = read(Path(archer["stock_manifest"]))["geometry"]["groups"][2]
        # LOD3 is small enough for a fast full topology/corner comparison. The
        # authored and cooked copies share a deliberate non-stock displacement.
        authored = copy.deepcopy(source)
        cooked = copy.deepcopy(source)
        for group in (authored, cooked):
            group["positions"] = [[p[0] + .02, p[1], p[2]] for p in group["positions"]]
        self.assertTrue(route.compare_lod(authored, cooked, 3)["passed"])
        with self.assertRaises(RuntimeError):
            route.compare_lod(source, cooked, 3)

    def test_corner_uv_seam_expands_without_losing_weighted_topology(self):
        archer = read(OUT / "qualification/archer-pairing-prep/manual-uvfix/three-lod-comparison.json")
        source = copy.deepcopy(read(Path(archer["stock_manifest"]))["geometry"]["groups"][2])
        source["corner_uvs"] = [[source["uv_layers"]["UVMap"][i] for i in triangle]
                               for triangle in source["triangles"]]
        source["uv_basis"] = "native_intended_before_export_preflip"
        # A seam on one face corner does not alter positions, weights or mesh
        # connectivity, but must remain visible to the native UV comparator.
        source["corner_uvs"][0][0] = [0.25, 0.75]
        expanded = route.expanded_corner_group(source)
        self.assertEqual(expanded["vertex_count"], 3 * source["triangle_count"])
        self.assertTrue(route.compare_lod(expanded, expanded, 3)["passed"])
        original = read(Path(archer["stock_manifest"]))["geometry"]["groups"][2]
        self.assertFalse(route.compare_lod(original, expanded, 3)["passed"])

    def test_actual_archer3_authored_native_readback(self):
        base = OUT / "authored-geometry/archer3"
        report, rb = read(base / "comparison.json"), read(base / "readback.json")
        source = read(Path(report["source_snapshot"]))
        cooked = read(Path(rb["decoded_manifest"]))
        self.assertEqual(report["status"], "authored_three_lod_geometry_qualified")
        for number, (a, b) in enumerate(zip(source["geometry"]["groups"],
                                         cooked["geometry"]["groups"]), 1):
            row = route.compare_authored_lod(route.expanded_corner_group(a), b, number)
            self.assertTrue(row["passed"])
            self.assertLessEqual(row["maximum_position_distance_m"], .001)

    def test_archer3_v5b_native_panel_rounding_only(self):
        base = OUT / "authored-geometry/archer3-v5b"
        spec, rb = read(base / "spec.json"), read(base / "readback.json")
        source = read(Path(spec["authored_snapshot"]))["geometry"]["groups"][0]
        native = read(Path(rb["decoded_manifest"]))["geometry"]["groups"][0]
        row = route.compare_authored_lod(route.expanded_corner_group(source), native, 1, 24)
        self.assertTrue(row["passed"])
        rounding = row["new_panel_native_weight_rounding"]
        self.assertEqual(rounding["changed_corners"], 69)
        self.assertEqual(rounding["dropped_one_count_influence_positions"], 2)
        self.assertEqual(rounding["maximum_8bit_weight_scalar_delta"], 2)
        self.assertFalse(row["raw_authored_weighted_corners_exact"])

        # A changed bone, a larger weight shift, and an unchanged-body mutation
        # must each be rejected even when panel rounding is allowed.
        panel_position = source["positions"][source["triangles"][-1][0]]
        panel_index = min(range(len(native["positions"])),
                          key=lambda i: sum((a - b) ** 2 for a, b in zip(panel_position, native["positions"][i])))
        wrong_bone = copy.deepcopy(native)
        wrong_bone["skin_indices"][panel_index][0] = 45
        with self.assertRaises(RuntimeError):
            route.compare_authored_lod(route.expanded_corner_group(source), wrong_bone, 1, 24)
        excessive = copy.deepcopy(native)
        excessive["skin_weights"][panel_index][0] += 10 / 255
        excessive["skin_weights"][panel_index][1] -= 10 / 255
        with self.assertRaises(RuntimeError):
            route.compare_authored_lod(route.expanded_corner_group(source), excessive, 1, 24)
        body_position = source["positions"][source["triangles"][0][0]]
        body_index = min(range(len(native["positions"])),
                         key=lambda i: sum((a - b) ** 2 for a, b in zip(body_position, native["positions"][i])))
        body_change = copy.deepcopy(native)
        body_change["skin_weights"][body_index][0] += 10 / 255
        body_change["skin_weights"][body_index][1] -= 10 / 255
        with self.assertRaises(RuntimeError):
            route.compare_authored_lod(route.expanded_corner_group(source), body_change, 1, 24)

    def test_spear4_native_coordinate_quantization_preserves_shape(self):
        base = OUT / "authored-geometry/spear4-v3"
        spec, rb = read(base / "spec.json"), read(base / "readback.json")
        source = read(Path(spec["authored_snapshot"]))["geometry"]["groups"][0]
        cooked = read(Path(rb["decoded_manifest"]))["geometry"]["groups"][0]
        row = route.compare_authored_lod(route.expanded_corner_group(source), cooked, 1)
        self.assertTrue(row["passed"])
        self.assertLess(row["maximum_position_distance_m"], .00105)

    def test_crossbow4_subpixel_native_position_merges_keep_corner_identity(self):
        base = OUT / "authored-geometry/crossbow4-v5b"
        spec, rb = read(base / "spec.json"), read(base / "readback.json")
        source = read(Path(spec["authored_snapshot"]))["geometry"]["groups"]
        cooked = read(Path(rb["decoded_manifest"]))["geometry"]["groups"]
        for number, (authored, native) in enumerate(zip(source, cooked), 1):
            row = route.compare_authored_lod(route.expanded_corner_group(authored), native,
                                             number, 24 if number == 1 else 0)
            self.assertTrue(row["passed"])
            self.assertEqual(row["source_unique_positions"] - row["compiled_unique_positions"], 2)
            self.assertTrue(row["triangle_topology_multiset_exact"])
            self.assertTrue(row["uv_corner_identity_keys_and_counts_exact"])

        altered = copy.deepcopy(cooked[2])
        altered["uv_layers"]["UVMap"][0][0] += .02
        self.assertFalse(route.compare_authored_lod(route.expanded_corner_group(source[2]),
                                                    altered, 3)["passed"])

    def test_actual_albedo_variant_rgm_keeps_stock_model_except_path(self):
        stock = read(OUT / "donors/decoded/archer02/dd37508a5894fb1dbf73/decoded-static.json")
        variant = read(OUT / "qualification/albedo-variants/v60a2/material-verification.json")
        record = variant_rgm_stock_except_path(stock, variant)
        self.assertEqual(len(record["only_changed_prefix_offsets"]), 3)
        self.assertTrue(record["tail_after_private_path_exact"])

    def test_archer2_v3_geometry_and_albedo_pair_inputs(self):
        pair = qualify_pair("archer2", OUT / "qualification/albedo-variants/v60a2/material-verification.json",
                            "archer2-v3")
        self.assertEqual(pair["status"], "qualified_media_pair_inputs_not_grafted")
        self.assertEqual(pair["native_lod_triangle_counts"], [1484, 522, 155])
        self.assertEqual(pair["only_intended_media_replacement"],
                         "art/scenario/garrison/v60a2/body/body.rrgeom")


if __name__ == "__main__": unittest.main()
