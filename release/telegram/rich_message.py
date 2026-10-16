# ======================================================
# 📨 TELEGRAM — Rich Message Composer (RedPanda port)
# Adapted from LuminaireProtocol/release/telegram/rich_message.py
# Bot API 10.1+ sendRichMessage
# ======================================================

from __future__ import annotations

import json
import os

import caption

# Varian yang dipakai Kernel-Builder. Key harus sama dengan
# "variant" yang ditulis stage.sh ke redpanda.json.
VARIANT_DISPLAY = {
    "BAKASU": "BakaSU",
    "KSUNEXT": "KernelSU-Next",
    "KSU": "KernelSU",
    "SUKISU": "SukiSU-Ultra",
    "VANILLA": "Vanilla",
}

LINKS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "links.json")


def load_links() -> dict:
    try:
        with open(LINKS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


LINKS = load_links()

BUG_REPORT_NOTE = (
    "If you encounter any issues or unexpected behavior, please report them "
    'through the <tg-button type="url" style="primary" url="{group_url}">RedPanda</tg-button> discussion group.'
)

# Nama grup default kalau TELEGRAM_GROUP tidak di-set (tanpa @).
DEFAULT_GROUP = "ArtecxyzArchive"


def variant_display(key: str) -> str:
    return VARIANT_DISPLAY.get(key, key)


def is_build_mode(env) -> bool:
    return env.get("RUN_MODE", "").strip().upper() == "BUILD"


VARIANT_ORDER = ["BAKASU", "KSUNEXT", "KSU", "SUKISU", "VANILLA"]


def variant_sort_key(key: str):
    base = key[:-len("_SUSFS")] if key.endswith("_SUSFS") else key
    try:
        return VARIANT_ORDER.index(base)
    except ValueError:
        return len(VARIANT_ORDER)


def commits_url(env) -> str:
    owner = env.get("KERNEL_SOURCE_OWNER", "").strip()
    repo = env.get("KERNEL_SOURCE_REPO", "").strip()
    branch = env.get("KERNEL_BRANCH", "").strip()
    if not (owner and repo and branch):
        return ""
    return f"https://github.com/{owner}/{repo}/commits/{branch}"


def changelogs_url(env) -> str:
    custom = env.get("CHANGELOG_URL", "").strip()
    if custom:
        return custom
    return commits_url(env)

def download_url(env) -> str:
    # Prioritas: input manual / hasil mirror PixelDrain > halaman Releases.
    custom = env.get("DOWNLOAD_URL", "").strip()
    if custom:
        return custom
    repo = env.get("GITHUB_REPOSITORY", "").strip()
    if not repo:
        return ""
    server = env.get("GITHUB_SERVER_URL", "").strip() or "https://github.com"
    return f"{server}/{repo}/releases"

def download_buttons(env) -> str:
    return button_row([("Download", download_url(env), "primary")])


def changelogs_buttons(env) -> str:
    # Download di atas, Changelogs di bawah (2 baris terpisah).
    rows = [
        download_buttons(env),
        button_row([("Changelogs", changelogs_url(env), "success")]),
    ]
    return "\n".join(r for r in rows if r)

def html_cell(text: str) -> str:
    return caption.html_escape(str(text)).replace("\n", " ").strip()


def variant_line(env) -> str:
    key = env.get("VARIANT", "").strip()
    has_susfs = key.endswith("_SUSFS")
    base = key[:-len("_SUSFS")] if has_susfs else key
    display = variant_display(base) if base else "N/A"
    parts = display
    ver = env.get("VARIANT_VERSION", "").strip()
    if ver:
        parts += f" {ver}"
    susfs_ver = env.get("SUSFS_VERSION", "").strip()
    if has_susfs or env.get("SUSFS_ENABLED", "") == "1" or susfs_ver:
        parts += " + SuSFS" + (f" {susfs_ver}" if susfs_ver else "")
    return parts


def build_info_table(env) -> str:
    variant = variant_line(env)
    lto_raw = env.get("LTO_MODE", "").strip()
    lto_display = caption.LTO_DISPLAY.get(lto_raw, lto_raw or "N/A")
    lto_chip = chip(lto_display, caption.LTO_CHIP_STYLE.get(lto_raw, ""))
    rows = [
        ("Kernel", html_cell("Linux " + (env.get("LINUX_VER", "").strip() or "N/A"))),
        ("Toolchain", html_cell(env.get("COMPILER_STRING", "").strip() or "N/A")),
        ("Variant", html_cell(variant)),
        ("LTO", lto_chip),
    ]
    body = "".join(f"<tr><td>{html_cell(k)}</td><td>{v}</td></tr>" for k, v in rows)
    return f"<table bordered>{body}</table>"


def button_row(buttons) -> str:
    if isinstance(buttons, tuple):
        buttons = [buttons]
    live = [(t, u, s) for t, u, s in buttons if u]
    if not live:
        return ""
    out = ["<tg-button-row>"]
    for text, url, style in live:
        style_attr = f' style="{style}"' if style else ""
        out.append(f'  <tg-button type="url"{style_attr} url="{url}">{text}</tg-button>')
    out.append("</tg-button-row>")
    return "\n".join(out)


def chip(text: str, style: str = "") -> str:
    style_attr = f' style="{style}"' if style else ""
    return f'<tg-button type="disabled"{style_attr}>{html_cell(text)}</tg-button>'


def release_url(key: str) -> str:
    base = key[:-len("_SUSFS")] if key.endswith("_SUSFS") else key
    return LINKS.get("variants", {}).get(base, "")


def variant_header(title: str, url: str = "") -> str:
    action = f'type="url" url="{url}"' if url else 'type="callback_data" data="x"'
    return (
        f'<tg-button-row><tg-button {action} '
        f'style="primary">{html_cell(title)}</tg-button></tg-button-row>'
    )


def core_features_folds() -> list:
    out = ['<tg-button-row><tg-button type="disabled">Core Features'
           "</tg-button></tg-button-row>", ""]
    for category, items in caption.FRAGMENT_FEATURES.items():
        out.append("<details>")
        out.append(f"<summary>{category}</summary>")
        out.append("")
        for item in items:
            if isinstance(item, tuple):
                label, subs = item
                out.append(f"- {label}: {', '.join(subs)}")
            else:
                out.append(f"- {item}")
        out.append("</details>")
    return out


def patch_fold(env) -> list:
    applied = [t for t in env.get("APPLIED_PATCHES", "").split(",") if t]
    rows = [
        caption.patch_active_line(env, t)
        for t in caption.patch_order(env)
        if t in applied
    ]
    if not rows:
        rows = ["SUSFS + KSU integration"]
    body = "".join(f"<tr><td>{html_cell(r)}</td></tr>" for r in rows)
    return [
        "<details>",
        "<summary>RedPanda Patches</summary>",
        "",
        f"<table bordered>{body}</table>",
        "</details>",
    ]


def addon_table(env, link_engine: bool = False) -> str:
    # RedPanda tidak pakai sistem addon Luminaire — tampilkan ringkas saja.
    variant = variant_display(env.get("VARIANT", "").strip()) if env.get("VARIANT", "").strip() else "N/A"
    susfs = env.get("SUSFS_VERSION", "").strip() or (
        "Enable" if env.get("SUSFS_ENABLED", "") == "1" else "N/A"
    )
    rows = [
        ("Variant", chip(variant, "primary")),
        ("SuSFS", chip(susfs, "success" if susfs not in ("N/A", "None") else "")),
    ]
    body = "".join(f"<tr><td>{html_cell(k)}</td><td>{v}</td></tr>" for k, v in rows)
    return f"<table bordered>{body}</table>"


def features_details(env) -> str:
    out = [
        "<details>",
        '<summary><tg-button type="disabled" style="primary">'
        "What's Inside?</tg-button></summary>",
        "",
    ]
    out += core_features_folds()
    out += patch_fold(env)
    out.append("</details>")
    return "\n".join(out)


def changelog_block(env) -> str:
    raw = env.get("CHANGELOG", "").strip()
    if not raw:
        return ""
    entries = [e.strip() for e in raw.split(";") if e.strip()]
    if not entries:
        return ""
    body = "\n".join(f"\u2022 {e}" for e in entries)
    return "```\n" + body + "\n```"


def banner_slideshow(banner_ids) -> str:
    slides = "\n".join(f'<img src="tg://photo?id={banner_id}" tg-spoiler/>' for banner_id in banner_ids)
    return f"<tg-slideshow>\n{slides}\n</tg-slideshow>"


def compose_markdown(env, variants_block, banner_ids=()) -> str:
    group = env.get("TELEGRAM_GROUP", "").strip() or DEFAULT_GROUP
    group_url = "https://t.me/{}".format(group)
    support_url = "https://sociabuzz.com/artecxyz"
    channel_url = "https://t.me/ArtecxyzArchive"

    build_mode = is_build_mode(env)

    parts = []
    if banner_ids:
        parts.append(banner_slideshow(banner_ids))
    if build_mode:
        parts += [build_info_table(env), variants_block]
    else:
        parts.append("# RedPanda GKI Kernel")
        parts.append(features_details(env))
        parts.append(build_info_table(env))
        parts.append(variants_block)

    cl = changelog_block(env)
    if cl:
        if not build_mode:
            parts.append(changelogs_buttons(env))
        parts.append(cl)
    elif not build_mode:
        parts.append(changelogs_buttons(env))

    if not build_mode:
        parts.append(button_row([
            ("Support", support_url, "primary"),
            ("Channel", channel_url, "primary"),
        ]))
        parts.append("> " + BUG_REPORT_NOTE.format(group_url=group_url))
        parts.append("\\#GKI \\#Kernel \\#RedPanda")

    return "\n\n".join(p for p in parts if p) + "\n"
