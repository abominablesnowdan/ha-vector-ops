from pathlib import Path
import json

ROOT = Path(__file__).parents[1]


def test_manifest_and_hacs_metadata():
    manifest = json.loads((ROOT / "custom_components/vector_ops/manifest.json").read_text())
    assert manifest["domain"] == "vector_ops"
    assert manifest["config_flow"] is True
    assert manifest["version"]
    assert json.loads((ROOT / "hacs.json").read_text())["name"] == "Vector Ops"


def test_expected_service_contracts_exist():
    text = (ROOT / "custom_components/vector_ops/__init__.py").read_text()
    for service in ("refresh_updates", "add_to_queue", "update_now", "run_pending", "clear_queue"):
        assert service in text
