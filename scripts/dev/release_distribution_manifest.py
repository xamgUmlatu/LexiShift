import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE_URL = "https://downloads.lexishift.app"
DEFAULT_BUCKET = "lexishift-distribution"


@dataclass(frozen=True)
class Asset:
    platform: str
    path: Path
    object_key: str
    url: str
    sha256: str
    size_bytes: int


def _repo_path(path: str) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return REPO_ROOT / candidate


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _parse_asset(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError(
            "assets must use PLATFORM=PATH, for example macos=dist/LexiShift.dmg"
        )
    platform, raw_path = value.split("=", 1)
    platform = platform.strip().lower()
    if not platform:
        raise argparse.ArgumentTypeError("asset platform must not be empty")
    path = _repo_path(raw_path.strip())
    return platform, path


def _published_at(value: str | None) -> str:
    if value:
        return value
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _build_asset(
    platform: str,
    path: Path,
    *,
    channel: str,
    version: str,
    base_url: str,
) -> Asset:
    if not path.is_file():
        raise FileNotFoundError(f"release asset not found: {path}")
    object_key = f"installers/{channel}/{version}/{platform}/{path.name}"
    return Asset(
        platform=platform,
        path=path,
        object_key=object_key,
        url=f"{base_url.rstrip('/')}/{object_key}",
        sha256=_sha256(path),
        size_bytes=path.stat().st_size,
    )


def _platform_metadata(asset: Asset, args: argparse.Namespace) -> dict[str, object]:
    metadata: dict[str, object] = {
        "url": asset.url,
        "sha256": asset.sha256,
        "size_bytes": asset.size_bytes,
    }
    if asset.platform == "macos":
        metadata["signed"] = args.macos_signed
        metadata["notarized"] = args.macos_notarized
    elif asset.platform == "windows":
        metadata["signed"] = args.windows_signed
    return metadata


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _write_checksums(path: Path, assets: list[Asset]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"{asset.sha256}  {asset.object_key}" for asset in assets]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _print_wrangler_commands(args: argparse.Namespace, assets: list[Asset]) -> None:
    for asset in assets:
        print(f"wrangler r2 object put {args.bucket}/{asset.object_key} --file {asset.path}")
    print(
        "wrangler r2 object put "
        f"{args.bucket}/releases/{args.channel}/latest.json --file {args.out_json}"
    )
    print(
        "wrangler r2 object put "
        f"{args.bucket}/checksums/{args.channel}/{args.version}/SHA256SUMS.txt "
        f"--file {args.checksums_out}"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate LexiShift hosted release metadata and checksums."
    )
    parser.add_argument("--version", required=True)
    parser.add_argument("--channel", default="beta", choices=("beta", "stable"))
    parser.add_argument("--asset", action="append", type=_parse_asset, default=[])
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--bucket", default=DEFAULT_BUCKET)
    parser.add_argument("--published-at")
    parser.add_argument("--release-notes-url")
    parser.add_argument("--macos-signed", action="store_true")
    parser.add_argument("--macos-notarized", action="store_true")
    parser.add_argument("--windows-signed", action="store_true")
    parser.add_argument(
        "--out-json",
        type=_repo_path,
    )
    parser.add_argument(
        "--checksums-out",
        type=_repo_path,
    )
    parser.add_argument("--print-wrangler-commands", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if not args.asset:
        parser.error("at least one --asset PLATFORM=PATH is required")
    if args.out_json is None:
        args.out_json = (
            REPO_ROOT / f"docs/test_outputs/release_manifests/{args.channel}_latest.json"
        )
    if args.checksums_out is None:
        args.checksums_out = (
            REPO_ROOT
            / "docs/test_outputs/release_manifests"
            / f"{args.channel}_{args.version}_SHA256SUMS.txt"
        )

    assets = [
        _build_asset(
            platform,
            path,
            channel=args.channel,
            version=args.version,
            base_url=args.base_url,
        )
        for platform, path in args.asset
    ]
    platforms = [asset.platform for asset in assets]
    if len(platforms) != len(set(platforms)):
        parser.error("release assets must use unique platform names")
    release_notes_url = args.release_notes_url or f"https://lexishift.app/releases/{args.version}/"
    manifest = {
        "schema_version": 1,
        "channel": args.channel,
        "version": args.version,
        "published_at": _published_at(args.published_at),
        "release_notes_url": release_notes_url,
        "platforms": {asset.platform: _platform_metadata(asset, args) for asset in assets},
    }

    _write_json(args.out_json, manifest)
    _write_checksums(args.checksums_out, assets)

    print(f"manifest: {args.out_json}")
    print(f"checksums: {args.checksums_out}")
    print("platforms: " + ", ".join(asset.platform for asset in assets))
    if args.print_wrangler_commands:
        _print_wrangler_commands(args, assets)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
