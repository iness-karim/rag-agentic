import json
from pathlib import Path
import sys


def read_jsonl(path: str) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(l) for l in lines if l.strip()]


keywords = json.loads(Path("eval/keywords.json").read_text(encoding="utf-8"))
rows = read_jsonl(sys.argv[1] if len(sys.argv) > 1 else "eval/results/generation_answers.jsonl")

ok = total = 0
for r in rows:
    if r["type"] == "sans_reponse":
        continue
    low = r["answer"].lower()
    good = "je ne sais pas" not in low and all(
        any(k.lower() in low for k in g) for g in keywords[r["id"]]
    )
    total += 1
    ok += good
    if not good:
        print("KO", r["id"])
print(f"Contenu correct : {ok}/{total}")