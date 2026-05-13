from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = [
    ROOT / "app" / "Overview.py",
    ROOT / "app" / "pages" / "1_RFM_Analysis.py",
    ROOT / "app" / "pages" / "2_Seller_Performance.py",
    ROOT / "app" / "pages" / "3_Cohort_Retention.py",
]


def main() -> int:
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL not set; skipping smoke test.", file=sys.stderr)
        return 0

    from streamlit.testing.v1 import AppTest

    failures: list[str] = []
    for page in PAGES:
        rel = page.relative_to(ROOT)
        print(f"--- {rel}")
        at = AppTest.from_file(str(page), default_timeout=180).run()
        if at.exception:
            for ex in at.exception:
                msg = f"{rel}: {ex.value}"
                print(f"  EXCEPTION: {msg}")
                failures.append(msg)
        else:
            print("  OK")

    if failures:
        print(f"\n{len(failures)} page(s) failed:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("\nAll pages OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
