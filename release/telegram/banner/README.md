# release/telegram/banner

Taruh 1 atau lebih file banner di sini:

- `banner/banner.png` (atau `.jpg` / `.jpeg`)

Catatan:

- Banner **hanya dipakai untuk postingan Release** (mode Channel),
  dipilih acak 1 file (lihat `post_card.py` → `find_banners()`).
- Mode Build (grup) sengaja **tanpa banner** agar ringan.
- File dari Luminaire (`banner.png` … `banner6.png`) **jangan** dipakai
  langsung — itu branding Luminaire. Ganti dengan banner RedPanda kamu.
- Kalau belum punya banner, kosongkan saja folder ini TAPI jangan
  jalankan Release sebelum ada minimal 1 banner (post akan gagal
  dengan pesan `banner requested but no ... found`).
