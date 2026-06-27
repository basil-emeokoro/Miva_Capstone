import json
from pathlib import Path

from scripts.docs.package_dissertation_assets import build_dissertation_assets


def test_dissertation_asset_pipeline_generates_manifest_and_core_assets(tmp_path: Path) -> None:
    output_root = tmp_path / "docs" / "dissertation"

    manifest = build_dissertation_assets(output_root=output_root)

    assert manifest["serps_version"] == "1.0"
    assert manifest["mode"] == "dissertation"
    assert manifest["generating_script"] == "scripts/docs/package_dissertation_assets.py"
    assert "Dissertation-Requirements.docx" in manifest["private_sources_excluded"]

    artefact_paths = {entry["path"] for entry in manifest["artefacts"]}
    assert any(path.endswith("fig_3_1_high_level_architecture.mmd") for path in artefact_paths)
    assert any(path.endswith("fig_3_7_entity_relationship_diagram.mmd") for path in artefact_paths)
    assert any(path.endswith("openapi.json") for path in artefact_paths)
    assert any(path.endswith("viva_scenario_catalog.json") for path in artefact_paths)
    assert any(path.endswith("captions.json") for path in artefact_paths)
    assert any(path.endswith("asset_index.json") for path in artefact_paths)
    assert any(path.endswith("dissertation_assets.zip") for path in artefact_paths)

    manifest_path = output_root / "manifests" / "manifest.json"
    assert manifest_path.exists()
    written_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert len(written_manifest["artefacts"]) >= 26
    assert written_manifest["asset_package"]["checksum_sha256"]
    assert all(entry["checksum_sha256"] for entry in written_manifest["artefacts"])
    assert all("status" in entry for entry in written_manifest["artefacts"])


def test_dissertation_asset_pipeline_exports_implementation_derived_content(tmp_path: Path) -> None:
    output_root = tmp_path / "docs" / "dissertation"
    build_dissertation_assets(output_root=output_root)

    er_source = (output_root / "chapter3" / "uml" / "fig_3_7_entity_relationship_diagram.mmd").read_text(encoding="utf-8")
    assert "candidates" in er_source
    assert "events" in er_source
    assert "fused_alerts" in er_source
    assert "policy_decisions" in er_source

    scenario_catalog = json.loads(
        (output_root / "chapter5" / "evaluation" / "viva_scenario_catalog.json").read_text(encoding="utf-8")
    )
    scenario_ids = {scenario["scenario_id"] for scenario in scenario_catalog["scenarios"]}
    assert "normal_candidate_behaviour" in scenario_ids
    assert "critical_combined" in scenario_ids

    openapi = json.loads((output_root / "chapter3" / "api" / "openapi.json").read_text(encoding="utf-8"))
    assert "/events" in openapi["paths"]
    assert "/vision/analyse-frame" in openapi["paths"]
    assert "/audio/analyse-features" in openapi["paths"]
    assert "/identity/analyse-confidence" in openapi["paths"]

    openapi_summary = json.loads((output_root / "chapter3" / "api" / "openapi_summary.json").read_text(encoding="utf-8"))
    assert openapi_summary["endpoint_count"] >= 4

    scenario_summary = json.loads(
        (output_root / "chapter5" / "evaluation" / "viva_scenario_summary.json").read_text(encoding="utf-8")
    )
    assert scenario_summary["scenario_count"] == 10
    assert scenario_summary["risk_distribution"]["Critical"] >= 1

    screenshot_plan = json.loads(
        (output_root / "chapter4" / "screenshots" / "screenshot_plan.json").read_text(encoding="utf-8")
    )
    assert screenshot_plan["status"] == "framework_ready_capture_not_executed"
    assert len(screenshot_plan["planned_screenshots"]) >= 8

    assert (output_root / "chapter5" / "charts" / "risk_distribution.svg").exists()
    assert (output_root / "dissertation_assets.zip").exists()
