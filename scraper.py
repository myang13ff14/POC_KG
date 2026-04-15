import asyncio
from playwright.async_api import async_playwright
from seed_products import BASE_URL


async def scrape_product(page, product_id: str, category: str) -> dict:
    """Scrape a single SmartFind product page. Returns a dict with product info and compat list."""
    url = f"{BASE_URL}{product_id}"
    await page.goto(url, wait_until="networkidle")
    await page.wait_for_timeout(3000)

    # Product name — div with obfuscated class _2HY62CqrRY9qBDZsKY1vfr
    name_el = await page.query_selector("._2HY62CqrRY9qBDZsKY1vfr")
    name = (await name_el.inner_text()).strip() if name_el else product_id

    # Part number — label inside ._3-dVNL2B0_fsaBKcHwUyeG
    part_el = await page.query_selector("._3-dVNL2B0_fsaBKcHwUyeG label")
    part_number = (await part_el.inner_text()).strip() if part_el else product_id

    # Click the COMPATIBILITY tab (third tab in #tabList)
    compat_tab = await page.query_selector("#tabList div:nth-child(3)")
    if compat_tab:
        await compat_tab.click()
        await page.wait_for_timeout(2000)

    # Compatible devices — first-column TD cells with rowspan in the compatibility table.
    # The table has class _2-R8boYe8O05a_RJibaHeH; TDs with the rowspan attribute hold
    # the device names (one device can map to multiple IDs, hence rowspan > 1).
    device_els = await page.query_selector_all("table._2-R8boYe8O05a_RJibaHeH td[rowspan]")
    devices = []
    for el in device_els:
        text = (await el.inner_text()).strip()
        if text:
            devices.append(text)

    return {
        "id": product_id,
        "name": name,
        "part_number": part_number,
        "category": category,
        "url": url,
        "compatible_devices": devices,
    }


async def scrape_all(products: list[dict]) -> list[dict]:
    """Scrape all products. Returns list of product dicts."""
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for product in products:
            print(f"Scraping {product['id']} ({product['category']})...")
            try:
                result = await scrape_product(page, product["id"], product["category"])
                print(f"  -> {result['name']}: {len(result['compatible_devices'])} compatible devices")
                results.append(result)
            except Exception as e:
                print(f"  -> ERROR scraping {product['id']}: {e}")
        await browser.close()
    return results
