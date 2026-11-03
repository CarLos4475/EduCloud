import json
from pathlib import Path

from campus.adapters.deepseek import DeepSeekProvider

root = Path(__file__).resolve().parents[2]
package, usage = DeepSeekProvider().generate_resource()
output = root / "apps/web/public/h0-generated.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps(package.model_dump(by_alias=True), ensure_ascii=False, indent=2),
    encoding="utf-8",
)
print(
    json.dumps(
        {
            "generatedResource": str(output.relative_to(root)),
            "schemaValid": True,
            "usage": usage,
        }
    )
)
