import json
import re
from pathlib import Path

RAW_DIR = Path("data/raw")
OUT_FILE = Path("data/processed/chunks.jsonl")
MAX_CHARS = 1500


def clean(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1", text)
    text = re.sub(r"https?://github\.com/[^\s/]+/[^\s/]+/(?:pull|issues)/(\d+)", r"#\1", text)
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\[docs\]", "", text)
    text = re.sub(r"(?<!\w):[a-z_]+:(?!\w)", "", text)
    text = re.sub(r"(?m)^\*\s+-\s+", "* ", text)   # <- la nouvelle ligne
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_sections(text: str) -> list[tuple[str, str]]:
    sections, title, lines = [], "Intro", []
    for line in text.split("\n"):
        if re.match(r"^#{1,6}\s", line):
            if "".join(lines).strip():
                sections.append((title, "\n".join(lines).strip()))
            title, lines = line.lstrip("# ").strip(), []
        else:
            lines.append(line)
    if "".join(lines).strip():
        sections.append((title, "\n".join(lines).strip()))
    return sections


def split_long(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    parts, current = [], ""
    for line in text.split("\n"):
        if current and len(current) + len(line) + 1 > max_chars:
            parts.append(current.strip())
            current = ""
        current += line + "\n"
    if current.strip():
        parts.append(current.strip())
    return parts


def main() -> None:
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    chunks = []
    for f in sorted(RAW_DIR.glob("*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            body = clean(r["body"])
            n = 0
            for title, section in split_sections(body):
                for part in split_long(section):
                    header = f"{r['repo']} {r['tag']} ({r['published_at'][:10]}) - {title}"
                    chunks.append({
                        "id": f"{r['repo'].replace('/', '__')}__{r['tag']}__{n}",
                        "repo": r["repo"],
                        "tag": r["tag"],
                        "published_at": r["published_at"][:10],
                        "url": r["url"],
                        "section": title,
                        "text": f"{header}\n{part}",
                    })
                    n += 1

    with OUT_FILE.open("w", encoding="utf-8") as out:
        for c in chunks:
            out.write(json.dumps(c, ensure_ascii=False) + "\n")

    lengths = [len(c["text"]) for c in chunks]
    print(f"{len(chunks)} chunks, longueur moyenne {sum(lengths) // len(lengths)}, max {max(lengths)}")


if __name__ == "__main__":
    main()