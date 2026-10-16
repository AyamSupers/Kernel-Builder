# ======================================================
# 📨 TELEGRAM — Post Payload Builder (RedPanda port)
# Adapted from LuminaireProtocol/release/telegram/post_card.py
# ======================================================

from __future__ import annotations

import glob
import json
import os
import random
import sys
import zipfile

import rich_message as rm

RICH_LIMIT = 32768
META_NAME = "redpanda.json"
BANNER_DIR = "banner"
BANNER_PATTERNS = ("*.png", "*.jpg", "*.jpeg")


def load_metas(stage_dir: str) -> list:
    metas = []
    for path in glob.glob(os.path.join(stage_dir, "**", "*.zip"), recursive=True):
        try:
            with zipfile.ZipFile(path) as archive:
                if META_NAME not in archive.namelist():
                    continue
                meta = json.loads(archive.read(META_NAME))
        except (zipfile.BadZipFile, ValueError, KeyError):
            continue
        meta["zip_path"] = path
        meta["zip_name"] = os.path.basename(path)
        metas.append(meta)
    metas.sort(key=lambda m: (rm.variant_sort_key(m.get("variant", "")), m.get("variant", "")))
    return metas


def shared_env(first: dict) -> dict:
    env = dict(os.environ)
    env.update(
        {
            "LINUX_VER": first.get("linux_ver", ""),
            "KERNEL_VERSION": first.get("kernel_version", ""),
            "KERNEL_BRANCH": first.get("kernel_branch", ""),
            "KERNEL_SOURCE_OWNER": first.get("kernel_source_owner", ""),
            "KERNEL_SOURCE_REPO": first.get("kernel_source_repo", ""),
            "COMPILER_STRING": first.get("compiler_string", ""),
            "LTO_MODE": first.get("lto_mode", ""),
            "VARIANT": first.get("variant", ""),
            "VARIANT_LABEL": first.get("variant_label", ""),
            "VARIANT_VERSION": first.get("variant_version", ""),
            "VARIANT_VERSION_DISPLAY": first.get("variant_version_display", ""),
            "KSU_TAG": first.get("ksu_tag", ""),
            "SUSFS_VERSION": first.get("susfs_version", ""),
            "SUSFS_ENABLED": first.get("susfs_enabled", ""),
            "APPLIED_PATCHES": first.get("applied_patches", ""),
            "PATCH_VERSIONS": first.get("patch_versions", ""),
        }
    )
    return env


def variant_title(meta: dict) -> str:
    key = meta.get("variant", "UNKNOWN")
    has_susfs = key.endswith("_SUSFS")
    label = meta.get("variant_label", "").strip()
    version = meta.get("variant_version_display", "").strip() or rm.variant_version_display(
        {"KSU_TAG": meta.get("ksu_tag", ""), "VARIANT_VERSION": meta.get("variant_version", "")}
    )
    if label:
        base_title = " ".join(p for p in (label, version) if p)
    else:
        base = key[: -len("_SUSFS")] if has_susfs else key
        base_title = " ".join(p for p in (rm.variant_display(base), version) if p)
    parts = [base_title]
    if has_susfs:
        parts.append(" ".join(p for p in ("SuSFS", meta.get("susfs_version", "")) if p))
    return " \u00b7 ".join(parts)


def variant_block(meta: dict, index: int, attach_zip: bool = True) -> str:
    lines = [
        rm.variant_header(variant_title(meta), rm.release_url(meta.get("variant", ""))),
        "",
    ]
    if attach_zip:
        lines += [f"![](tg://document?id=zip{index})", ""]
    return "\n".join(lines)


def attachment_specs(metas: list, banners: list, attach_zip: bool = True) -> list:
    specs = [f"banner_file{i}=@{path}" for i, path in enumerate(banners, 1)]
    if not attach_zip:
        return specs
    for i, meta in enumerate(metas, 1):
        specs.append(f"zip_{i}=@{meta['zip_path']};filename={meta['zip_name']}")
    return specs


def find_banners() -> list:
    base = os.path.join(os.path.dirname(os.path.abspath(__file__)), BANNER_DIR)
    banners = sorted({p for pattern in BANNER_PATTERNS for p in glob.glob(os.path.join(base, pattern))})
    if not banners:
        sys.exit(f"post_card: banner requested but no {BANNER_PATTERNS} found in {base}")
    random.shuffle(banners)
    return banners


def banner_requested() -> bool:
    return os.environ.get("POST_BANNER", "0").lower() in ("1", "true", "yes")


def mirror_available() -> bool:
    # Kalau link mirror (PixelDrain/manual) ada, file zip tidak perlu
    # dilampirkan ke Telegram — cukup tombol Download.
    return bool(os.environ.get("DOWNLOAD_URL", "").strip())


def build_payload(metas: list, env: dict, banner_count: int, attach_zip: bool = True) -> dict:
    blocks = "\n".join(variant_block(m, i, attach_zip) for i, m in enumerate(metas, 1))
    banner_ids = [f"banner{i}" for i in range(1, banner_count + 1)]
    markdown = rm.compose_markdown(env, blocks, banner_ids=banner_ids)
    media = [
        {"id": f"banner{i}", "media": {"type": "photo", "media": f"attach://banner_file{i}"}}
        for i in range(1, banner_count + 1)
    ]
    if attach_zip:
        for i in range(1, len(metas) + 1):
            media.append({"id": f"zip{i}", "media": {"type": "document", "media": f"attach://zip_{i}"}})
    return {"markdown": markdown, "media": media}


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit("usage: post_card.py <stage-dir> <out-payload-json> <out-attachments-file>")
    stage_dir, payload_path, attachments_path = sys.argv[1:4]

    metas = load_metas(stage_dir)
    if not metas:
        sys.exit("post_card: no staged variants found")

    banners = find_banners() if banner_requested() else []
    attach_zip = not mirror_available()
    payload = build_payload(metas, shared_env(metas[0]), len(banners), attach_zip)
    if len(payload["markdown"]) > RICH_LIMIT:
        sys.exit(f"post_card: {len(payload['markdown'])} chars exceeds {RICH_LIMIT}")

    with open(payload_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    with open(attachments_path, "w", encoding="utf-8") as f:
        f.write("\n".join(attachment_specs(metas, banners, attach_zip)) + "\n")

    print(
        f"[info] post_card: {len(metas)} variant(s), banners={len(banners)}, attach_zip={int(attach_zip)}, {len(payload['markdown'])} chars (limit {RICH_LIMIT}) \u2705",
        file=sys.stderr,
        flush=True,
    )


if __name__ == "__main__":
    main()
