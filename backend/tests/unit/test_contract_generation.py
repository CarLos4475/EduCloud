import importlib.util
from pathlib import Path

from campus.domain.contracts import SourceRef


def test_generator_preserves_nullable_array_items_and_exact_protocol_version() -> None:
    path = Path(__file__).resolve().parents[2] / "scripts" / "generate_contracts.py"
    spec = importlib.util.spec_from_file_location("contract_generator", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.type_for({"type": "null"}) == "null"
    assert module.type_for({"const": 1}) == "1"
    assert (
        module.type_for(
            {
                "type": "array",
                "items": {"anyOf": [{"type": "string"}, {"type": "null"}]},
            }
        )
        == "(string | null)[]"
    )
    rendered = module.render_types(
        {
            "components": {
                "schemas": {"SourceRef": SourceRef.model_json_schema(by_alias=True)}
            }
        }
    )
    assert "materialId: string" in rendered
    assert "quote?: string | null" in rendered
