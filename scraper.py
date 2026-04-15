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

    # Compatible devices — iterate all rows of the compatibility table.
    # Description cell has rowspan when one device maps to multiple machine-type IDs.
    rows = await page.query_selector_all("table._2-R8boYe8O05a_RJibaHeH tr")
    devices = []
    current_desc = ""
    for row in rows:
        cells = await row.query_selector_all("td")
        if not cells:
            continue

        first_attr = await cells[0].get_attribute("rowspan")
        if first_attr:
            # First cell is the description
            current_desc = (await cells[0].inner_text()).strip()
            id_cell = cells[1] if len(cells) > 1 else None
            footnote_cell = cells[2] if len(cells) > 2 else None
        else:
            # Continuation row — description carried over from rowspan
            id_cell = cells[0] if len(cells) > 0 else None
            footnote_cell = cells[1] if len(cells) > 1 else None

        machine_type = (await id_cell.inner_text()).strip() if id_cell else ""
        footnote = (await footnote_cell.inner_text()).strip() if footnote_cell else ""

        if current_desc and machine_type:
            devices.append({
                "name": current_desc,
                "machine_type": machine_type,
                "footnote": footnote,
            })

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
