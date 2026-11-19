# LANDSCAPE_GO — FG-1 Strategy Game and Two Scientific Landscape Atlases

**Public, owner-authorized clean-history edition · 19 November 2026 · experimental v4 (not a certified `v4.0.0` tag).**

**Languages:** [English](README.md) · [Українська](README_UK.md) · [Русский](README_RU.md)

LANDSCAPE_GO is an offline strategy game inspired by Go but governed by its own **FG-1 / Scoring v0.2** rules. It is **not classical Go**, not the separate Dynamic Landscape model, and not an AlphaGo-strength computer opponent. Stones occupy **numbered cells, not line intersections**. Captured cells freeze permanently; voluntary passing is forbidden. A primary balanced value **V=0** does **not** establish the full lexicographic **U=0**. For large boards with no proof, global minimax remains **unknown**.

## Play

1. Install **Python 3.11 or later**, with **Tkinter** (normally included on Windows; install `python3-tk` on many Linux systems). No extra pip packages are needed for normal gameplay.
2. Extract the archive to a new folder. Windows: double-click `START_LANDSCAPE_GO_WINDOWS.bat`; Linux/macOS: `python3 LANDSCAPE_GO.py`.
3. Choose **English / Українська / Русский**, field size and an FG-1 mode: **Original**, **Dual Priority** or **Monochrome**. The game provides person-versus-person/computer, undo, save/load and an Atlas viewer.
4. Scientific catalog filters are built into the game; the printable Atlases are **curated selections**, not every research matrix ever studied.

Example optional CLI: `python LANDSCAPE_GO.py --mode mono --size 3 --verify --cli`.

## Two printable original Atlases (A4)

| Atlas | Source file | Contents |
|---|---|---|
| Main | `ATLAS/PRINT/PRINT_PREVIEW_37_LANDSCAPES.html` | 37 fields 3×3–19×19 + cover (38 pages) |
| Signed/Monochrome | `ATLAS/SIGNED_MONO/PRINT_PREVIEW_A4.html` | 18 fields (18 pages) |

Open either HTML file in a browser, press **Ctrl+P**, select **A4 portrait, 100%**, and disable browser print headers/footers. The exported layouts passed PDF geometry checks on Windows and Ubuntu; the owner has **reported accepting physical print proofs**, including 19×19 at approximately 7 pt. See `ATLAS/PRINT/PRINT_GUIDE_UK.md` / `PRINT_GUIDE_RU.md`.

## Full FG-1 rules

Original complete rules: [`SOURCE_DOCUMENTS/LANDSCAPE_GO_COMPLETE_RULES_RU.md`](SOURCE_DOCUMENTS/LANDSCAPE_GO_COMPLETE_RULES_RU.md). Complete Ukrainian translation: [`SOURCE_DOCUMENTS/LANDSCAPE_GO_COMPLETE_RULES_UK.md`](SOURCE_DOCUMENTS/LANDSCAPE_GO_COMPLETE_RULES_UK.md). Short Russian/Ukrainian guides are under `ATLAS/PRINT/`.

## Data and authenticity

Includes **45 original game DATA JSON** and **two original Atlas catalog JSON** files. The historical private Git repository, raw research ZIP/GZIP/SQLite archives and undocumented scientific proofs are **not** included. Game source, Atlas catalog numbers and 55 printable scientific tables (7,797 numeric cells) were preserved from the verified private candidate; only public-facing instructions and non-table preview notices were updated. Full original mathematical validation is **not** claimed for unproved large-board cases.

Verify integrity against the complete file-by-file `SHA256SUMS.txt` before redistribution. The **ZIP's own** SHA-256 is supplied **outside the ZIP** as `DOWNLOAD_SHA256.txt`.

## License and permission

Official software license: **unmodified [PolyForm Strict 1.0.0](LICENSE)**. Existing `DATA_LICENSE.md` and `COMMERCIAL_LICENSE.md` remain unchanged. The owner's **[additional permission for free unchanged copies](ADDITIONAL_PERMISSION_EN.md)** expressly allows free noncommercial copying and giving away **complete, unchanged** author-approved editions and unchanged printed Atlas sheets, keeping notices. No public redistribution of modified protected code, altered copyrighted Atlases or commercial sale is granted by that additional permission. Translations: [Українська](ADDITIONAL_PERMISSION_UK.md), [Русский](ADDITIONAL_PERMISSION_RU.md). Historic valid MIT grants for their respective old copies remain unaffected; mathematics and independently developed methods are not claimed as exclusive intellectual property.

© 2026 Oleh Tymofiienko, to the extent of rights held by the licensor. Author contact: https://github.com/OlehTymofiienko . Owner reports that physical printing and formal rights review have been completed; this repository does not include an independent legal opinion. Provided **as is**.
