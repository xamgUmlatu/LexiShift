#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from pack_source_url_audit_support import (  # noqa: E402
    build_pack_source_url_audit_report,
    parse_args,
    print_summary,
    render_markdown,
)


def main() -> int:
    args = parse_args()
    report = build_pack_source_url_audit_report(
        manifest_path=None if args.manifest_url else args.manifest_path,
        manifest_url=args.manifest_url,
        pack_ids=args.pack_ids,
        pack_kinds=args.pack_kinds,
        include_archive=not bool(args.skip_archive),
        timeout_seconds=max(1.0, float(args.timeout_seconds)),
    )

    json_out = args.json_out.expanduser().resolve(strict=False)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    markdown = render_markdown(report)
    markdown_out = args.markdown_out.expanduser().resolve(strict=False)
    markdown_out.parent.mkdir(parents=True, exist_ok=True)
    markdown_out.write_text(markdown, encoding="utf-8")

    print_summary(report)
    print(f"json_output: {json_out}")
    print(f"markdown_output: {markdown_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
