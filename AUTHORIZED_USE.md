# Authorized use

This repository is a bounded local research range for investigating one pinned ARTEX Docker image. Run the PoC only against the included loopback lab or a system you are expressly authorized to test. Do not use it against third-party ARTEX consoles.

`poc.py` sends only a fixed `id` request to one of two loopback ports listed in `profiles.json`. It accepts no command or URL argument, does not inspect or control Docker, and reports success only from fresh HTTP output. The image digest and profile registry identify tested builds; they do not authorize testing other systems. The proof establishes container root execution, not host compromise.

Gunakan PoC ini hanya pada lab lokal yang disertakan atau sistem yang Anda berwenang uji. Jangan kirim pemicu backdoor ke konsol ARTEX milik pihak lain. Bukti yang ditampilkan adalah akses root di dalam kontainer, bukan pada host.
