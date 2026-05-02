"""Capture full-page screenshots of every Streamlit page.

Assumes the app is already running locally at http://localhost:8765
(start it with `streamlit run app/Overview.py --server.port=8765`).

Output goes to docs/screenshots/{overview,rfm,seller_performance,cohort_retention}.png.
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:8765"
OUT = Path(__file__).resolve().parent.parent / "docs" / "screenshots"

PAGES = [
    ("overview.png", f"{BASE}/"),
    ("rfm.png", f"{BASE}/RFM_Analysis"),
    ("seller_performance.png", f"{BASE}/Seller_Performance"),
    ("cohort_retention.png", f"{BASE}/Cohort_Retention"),
]


def _wait_for_render(page) -> None:
    """Wait until Streamlit has finished rendering (no running indicator, no skeletons)."""
    page.wait_for_selector("[data-testid='stAppViewContainer']", timeout=60_000)
    # Wait for the "Running" status pill to disappear, if present.
    try:
        page.wait_for_function(
            "() => !document.querySelector('[data-testid=\"stStatusWidget\"]')"
            " || !document.querySelector('[data-testid=\"stStatusWidget\"]').innerText.toLowerCase().includes('running')",
            timeout=90_000,
        )
    except Exception:
        pass
    # Wait for skeleton placeholders to disappear.
    try:
        page.wait_for_function(
            "() => document.querySelectorAll('[class*=\"stSkeleton\"]').length === 0",
            timeout=90_000,
        )
    except Exception:
        pass
    page.wait_for_timeout(2500)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page = context.new_page()
        # Warm cache: visit every URL once before capturing so subsequent loads are fast.
        for _, url in PAGES:
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            _wait_for_render(page)
        for filename, url in PAGES:
            target = OUT / filename
            print(f"-> {url}")
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            _wait_for_render(page)
            page.screenshot(path=str(target), full_page=True)
            print(f"   saved {target.relative_to(OUT.parent.parent)} ({target.stat().st_size // 1024} KB)")
        browser.close()


if __name__ == "__main__":
    main()
