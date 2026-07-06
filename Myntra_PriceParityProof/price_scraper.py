import requests
# THE POSTMAN. You say: "go get me this webpage URL"
# It sends an HTTP request and returns the HTML as text.
# Fast (1-2 seconds). Gets blocked on JavaScript-heavy sites.
# Think of it as: curl in Python.

from bs4 import BeautifulSoup
# THE HTML READER. Takes the wall of HTML text the postman brought
# and turns it into a searchable tree structure.
# soup.find('div', class_='price') = "find the first div that has class='price'"
# soup.select_one('.Nx9bqj') = CSS selector, same idea
# Without this, you'd have to search raw text with regex = painful.

import pandas as pd
# For reading your Excel file and saving/appending to CSV.

import time
import random
# time.sleep(8) = pause execution for 8 seconds
# random.uniform(6, 12) = random float between 6.0 and 12.0
# WHY: robots click at exact intervals. Humans don't.
# random.uniform(6,12) makes each wait slightly different = human-like

import re
# Regular expressions. Pattern matching in strings.
# re.findall(r'\d+', 'Rs.1299 save 200') = ['1299', '200']
# re.search(r'"price":(\d+)', json_text) = finds price in JSON

import os
import json
from datetime import datetime, date
from urllib.parse import urlparse

# Selenium - controls a real Chrome browser
# Used for JavaScript-heavy sites (Flipkart, Max Fashion, Off Duty)
# When requests gets a blank page, Selenium gets the real thing
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.service import Service
    SELENIUM_OK = True
except ImportError:
    SELENIUM_OK = False
    print("WARNING: pip install selenium webdriver-manager")

os.makedirs("data", exist_ok=True)


# ═══════════════════════════════════════════════════════════════
# SECTION 2: TIMING - THE MOST IMPORTANT ANTI-BOT SETTING
#
# WHY TIMING MATTERS:
# A real human visits 1 page every 10-30 seconds.
# A bot visits 100 pages per second.
# Websites measure request frequency. If too fast = blocked.
#
# OUR STRATEGY:
# - 6-12 seconds between Myntra and competitor (same product)
# - 10-18 seconds between different products
# - Random within each range (humans aren't precise)
# - Extra long sleep if we hit a rate limit (429 status code)
# ═══════════════════════════════════════════════════════════════

SLEEP_BETWEEN_PLATFORMS = (5, 9)   # seconds - between myntra and competitor
SLEEP_BETWEEN_PRODUCTS  = (9, 12)  # seconds - between each product
SLEEP_RATE_LIMITED      = (90, 180) # seconds - if server says "slow down"
# WHY 90-180 FOR RATE LIMIT: If a server sends 429 (too many requests),
# waiting less than 90 seconds usually doesn't help. They typically
# reset rate limits on a per-minute or per-5-minute basis.


# ═══════════════════════════════════════════════════════════════
# SECTION 3: BROWSER HEADERS POOL
#
# WHAT IS A HEADER:
# When Chrome visits amazon.in, it sends a message saying:
# "Hi, I'm Chrome 124 on Windows 10, please send me this page"
# This message is called HTTP headers. The key part is User-Agent.
#
# PROBLEM: Python's requests sends:
# "Hi, I'm python-requests/2.31" - websites see this and block immediately.
#
# SOLUTION: We pretend to be real browsers by sending real browser headers.
#
# WHY A POOL OF 6: If we use the SAME header every request, the website
# sees "Chrome 124 on Windows 10 has visited 66 times in 20 minutes"
# = obvious bot. Rotating through 6 different browser identities looks
# like 6 different people visiting.
# ═══════════════════════════════════════════════════════════════

HEADERS_POOL = [
    {   # Chrome 124 on Windows - most common browser worldwide
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
    },
    {   # Chrome 123 on Mac
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    },
    {   # Firefox 124 on Windows
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    },
    {   # Safari on iPhone - mobile UA sometimes bypasses desktop bot checks
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {   # Chrome on Linux
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    },
    {   # Edge on Windows
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    },
]

def get_headers():
    """Pick random headers from pool. Called fresh for every request."""
    return random.choice(HEADERS_POOL)


# ═══════════════════════════════════════════════════════════════
# SECTION 4: CATEGORY-AWARE PRICE FLOORS
#
# THE PROBLEM WE SOLVED:
# Selenium on Flipkart grabbed Rs.107, Rs.150, Rs.100 for shirts
# and shoes. These are NOT product prices. They are:
# - Delivery charges (Rs.40-99)
# - "EMI from Rs.X" text
# - Discount save amounts ("Save Rs.150")
# - Prices of DIFFERENT products in a recommendation carousel
#
# THE FIX:
# Every product category has a realistic minimum price.
# A shirt cannot cost Rs.107. A shoe cannot cost Rs.100.
# If the extracted price is below the category floor, it's garbage.
# We reject it and keep looking.
#
# WHY NOT JUST USE Rs.200 FOR EVERYTHING:
# A lipstick can genuinely cost Rs.150. A face cream can be Rs.180.
# A flat floor would reject real beauty prices.
# Category-specific floors are more precise.
# ═══════════════════════════════════════════════════════════════

CATEGORY_FLOORS = {
    # Category name (lowercase) : minimum realistic price in Rs.
    "clothing":    400,   # shirts, tshirts, jeans, kurtas - nothing legit under Rs.400
    "footwear":    300,   # shoes, sandals, flip flops - nothing legit under Rs.300
    "ethnic wear": 400,   # kurtas, sets - nothing legit under Rs.400
    "lingerie":    200,   # bras, innerwear - can be lower
    "makeup":      150,   # lipstick, eyeliner - genuinely cheap products exist
    "skincare":    99,    # face cream, serum - small products can be under Rs.200
    "default":     150,   # fallback for any unlisted category
}

def get_floor(category):
    """Get minimum valid price for a category."""
    return CATEGORY_FLOORS.get(category.lower().strip(), CATEGORY_FLOORS["default"])


# ═══════════════════════════════════════════════════════════════
# SECTION 5: PRICE EXTRACTION
#
# CORE CHALLENGE:
# A product page contains MANY numbers. Example on a shirt page:
# "MRP Rs.2,999  | Now Rs.1,798 | Save Rs.1,201 | 4.2★ | 234 reviews
#  EMI from Rs.150/month | Delivery by May 7 | Size: 38, 40, 42"
#
# We want: 1798 (the selling price, what you actually pay)
# Not:     2999 (MRP - crossed out), 1201 (savings), 4.2 (rating),
#          234 (review count), 150 (EMI amount), 7 (delivery date),
#          38/40/42 (sizes)
#
# STRATEGY:
# 1. Strip unit-price patterns first (Rs.3.51/ml)
# 2. Find ALL numbers in realistic price range
# 3. Apply category floor (no shirt under Rs.400)
# 4. Return the MINIMUM valid price = selling price
#    (because MRP is always higher than selling price)
#
# WHY MINIMUM:
# Page shows: MRP Rs.2999, Selling Rs.1798
# Both pass the floor check. Minimum = 1798 = correct.
# ═══════════════════════════════════════════════════════════════

def extract_price(text, floor=99):
    """
    Extract the selling price from any text string.

    Args:
        text: raw text from HTML element
        floor: minimum valid price (default 99, override per category)

    Returns:
        float price or None

    Examples:
        extract_price("₹1,299")              -> 1299.0
        extract_price("MRP ₹1999 Now ₹1299") -> 1299.0  (minimum)
        extract_price("EMI ₹150/month", 400) -> None    (150 < floor 400)
        extract_price("Save ₹200", 400)      -> None    (200 < floor)
        extract_price("USP: ₹3.51/ml")       -> None    (filtered by pattern)
        extract_price("")                     -> None
    """
    if not text:
        return None

    text = str(text)

    # Step 1: Remove unit-price patterns BEFORE extracting numbers
    # "₹3.51/ml" would give us 3.51 which is way below any floor
    # but we need to remove it explicitly to be safe
    text = re.sub(r'₹[\d.,]+\s*/\s*(ml|g|gm|kg|l|litre|piece|pc)', '', text, flags=re.I)
    text = re.sub(r'USP\s*:?\s*₹[\d.,]+', '', text, flags=re.I)
    # Remove EMI patterns - "EMI from ₹150" or "₹150/month"
    text = re.sub(r'EMI\s+(?:from\s+)?₹[\d.,]+', '', text, flags=re.I)
    text = re.sub(r'₹[\d.,]+\s*/\s*month', '', text, flags=re.I)

    # Step 2: Clean up currency symbols so we just have numbers
    cleaned = text.replace('₹', ' ').replace(',', '').replace('Rs.', ' ').replace('Rs', ' ')

    # Step 3: Find all number patterns
    # \b = word boundary (don't match "2" from middle of "1299.2")
    # \d{2,6} = 2 to 6 digit number (10 to 999999)
    # (?:\.\d{1,2})? = optional decimal (for 299.99 style prices)
    matches = re.findall(r'\b(\d{2,6}(?:\.\d{1,2})?)\b', cleaned)

    # Step 4: Filter to valid price range
    valid_prices = []
    for m in matches:
        try:
            p = float(m)
            if floor <= p <= 50000:   # floor = category minimum, ceiling = Rs.50,000
                valid_prices.append(p)
        except ValueError:
            continue

    if not valid_prices:
        return None

    # Step 5: Return minimum = selling price (MRP is always higher)
    return min(valid_prices)


# ═══════════════════════════════════════════════════════════════
# SECTION 6: PAGE TYPE DETECTION
#
# THE ROOT CAUSE OF BAD FLIPKART DATA:
# When Selenium opened some Flipkart URLs, instead of landing on
# the product page, it landed on a SEARCH RESULTS / LISTING PAGE.
# The #slot-list-container in your DevTools output confirmed this.
# slot-list-container = the grid of many products = listing page.
#
# On a listing page, there are prices from MANY products.
# Our scraper grabbed the cheapest one = totally wrong product.
#
# FIX: Detect which type of page we're on FIRST.
# Product page: has one main price, product title, buy button
# Listing page: has a grid of many products with many prices
#
# If we detect a listing page, we return None immediately.
# Better to fail cleanly than return wrong data silently.
# ═══════════════════════════════════════════════════════════════

def is_product_page(soup, platform):
    """
    Returns True if this looks like a product detail page.
    Returns False if it looks like a listing/search page.

    HOW TO TELL THE DIFFERENCE:
    Product page: "Add to Cart" button, single product title, one price
    Listing page: grid of products, multiple prices, no "Add to Cart"
    """
    page_text = soup.get_text().lower()

    if platform == "flipkart":
        # Listing page indicators - if any of these exist, we're on wrong page
        listing_signals = [
            soup.find(id='slot-list-container'),      # grid listing container
            soup.find(class_=re.compile(r'_1YokD2')), # search results class
            soup.find(class_=re.compile(r'_2kHMtA')), # another listing class
        ]
        if any(listing_signals):
            return False

        # Product page indicators - if these exist, we're on right page
        product_signals = [
            'add to cart' in page_text,
            soup.find(class_=re.compile(r'aMaAEs')),  # product title class
            soup.find(class_=re.compile(r'Nx9bqj')),  # price class on product page
        ]
        return any(product_signals)

    # For other platforms, assume product page unless proven otherwise
    return True


# ═══════════════════════════════════════════════════════════════
# SECTION 7: PLATFORM-SPECIFIC PRICE EXTRACTORS
#
# EVERY WEBSITE STRUCTURES THEIR HTML DIFFERENTLY.
# Amazon puts price in: <span id="priceblock_ourprice">
# Flipkart puts price in: <div class="Nx9bqj CxhGGd">
# Myntra puts price in: <span class="pdp-price"><strong>
#
# We write specific selectors for each.
# When selectors break (sites redesign), you fix them via DevTools:
# 1. Open product page in Chrome
# 2. Right-click the price -> Inspect
# 3. Note the element's class/id
# 4. Update the selector in the relevant section below
#
# YOUR DEVTOOLS FINDING FOR FLIPKART (from your message):
# Class: "v1zwn21l v1zwn20 _1psv1zeb9 _1psv1ze0"
# BUT: This was on a LISTING page (slot-list-container)
# The PRODUCT page class is: Nx9bqj (confirmed from multiple sources)
# ═══════════════════════════════════════════════════════════════

def get_price_from_page(soup, platform, category="default"):
    """
    Extract product price from parsed HTML.

    Args:
        soup: BeautifulSoup object of the page
        platform: 'myntra', 'amazon', 'flipkart', etc.
        category: product category for floor price

    Returns:
        float price or None
    """
    floor = get_floor(category)
    price = None

    # ── MYNTRA ────────────────────────────────────────────────
    if platform == "myntra":
        # Myntra is React. Prices load via JavaScript.
        # requests gets an empty shell. Selenium gets the real page.
        # BUT: Myntra sometimes embeds price data in JSON inside <script> tags.
        # We try that first (faster than waiting for Selenium to find CSS elements).

        # Method 1: JSON in script tags (fastest when it works)
        for script in soup.find_all('script'):
            t = script.string or ''
            # Look for "discountedPrice":1299 pattern in the JSON
            m = re.search(r'"discountedPrice"\s*:\s*(\d+)', t)
            if m:
                p = float(m.group(1))
                if floor <= p <= 50000:
                    return p
            # Backup pattern
            m = re.search(r'"price"\s*:\s*(\d+)', t)
            if m:
                p = float(m.group(1))
                if floor <= p <= 50000:
                    return p

        # Method 2: CSS selectors (work when page is JS-rendered by Selenium)
        for sel in [
            'span.pdp-price strong',    # main price - strong tag inside pdp-price
            '.pdp-price',               # price container
            'span[class*="pdp-price"]', # partial match if class changes slightly
        ]:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── AMAZON ────────────────────────────────────────────────
    elif platform == "amazon":
        # Amazon is the MOST scraper-friendly platform.
        # Uses stable IDs that rarely change.
        # requests usually works (no Selenium needed most of the time).
        # amzn.in short URLs auto-redirect to full amazon.in URLs.

        # Method 1: Stable IDs (most reliable)
        for id_ in [
            'priceblock_ourprice',    # standard buying price
            'priceblock_dealprice',   # discounted/deal price
            'price_inside_buybox',    # price in the "buy box" section
            'corePrice_feature_div',  # newer Amazon layout
        ]:
            el = soup.find(id=id_)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

        # Method 2: Class selectors
        for cls in ['a-price-whole', 'a-offscreen']:
            el = soup.find(class_=cls)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

        # Method 3: Any span with ₹ symbol and short text (just the price, not description)
        # This catches Amazon layout variations
        for span in soup.find_all('span'):
            t = span.get_text().strip()
            if '₹' in t and len(t) < 15:  # short = just a price, not a description
                p = extract_price(t, floor)
                if p:
                    return p

    # ── FLIPKART ──────────────────────────────────────────────
    elif platform == "flipkart":
        # IMPORTANT: Always check we're on a PRODUCT page first.
        # If on listing page, return None immediately.
        # Listing page prices = wrong products = garbage data.
        if not is_product_page(soup, "flipkart"):
            print("DETECTED LISTING PAGE - not a product page, returning None")
            return None

        # Flipkart rotates class names every few months (anti-scraping).
        # Current class as of May 2026: Nx9bqj
        # When this breaks: DevTools -> right-click PRODUCT price -> Inspect
        # Find new class name, add it as first item in list below.

        for sel in [
            'div.Nx9bqj.CxhGGd',         # Current May 2026 - final selling price
            'div.v1zwn21l.v1zwn20._1psv1zeb9._1psv1ze0',
            'div.Nx9bqj',                 # same class without secondary
            'div[class*="Nx9bqj"]',       # partial match - survives minor class changes
            '._30jeq3._16Jk6d',           # older class combination
            '._30jeq3',                   # even older fallback
        ]:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

        # Nuclear fallback: find ALL price-like text, take the most common value
        # This works even if ALL class names change because prices always contain ₹
        # We take most common (not minimum) because minimum might be EMI/shipping
        all_prices = []
        for el in soup.find_all(string=re.compile(r'₹\s*[\d,]+')):
            p = extract_price(str(el), floor)
            if p:
                all_prices.append(p)
        if all_prices:
            from collections import Counter
            # Most frequent price = selling price (appears in multiple places on page)
            # Not minimum here because floor already eliminates low garbage values
            return Counter(all_prices).most_common(1)[0][0]

    # ── MAX FASHION ───────────────────────────────────────────
    elif platform == "maxfashion":
        # Max Fashion (maxfashion.in) - moderate bot detection
        # requests gets blocked sometimes, Selenium usually works
        # Uses somewhat standard class names

        # JSON-LD structured data (standardized SEO format, very reliable)
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string or '{}')
                t = json.dumps(data)
                m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', t)
                if m:
                    p = float(m.group(1))
                    if floor <= p <= 50000:
                        return p
            except:
                continue

        for sel in [
            'span.price',
            '.product-price span',
            'span[class*="price"]',
            '.pdpPrice',
            '[class*="selling-price"]',
        ]:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── PUMA ──────────────────────────────────────────────────
    elif platform == "puma":
        # Puma India (in.puma.com) uses JSON-LD - very reliable
        # requests works most of the time

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                t = json.dumps(json.loads(script.string or '{}'))
                for field in ['"price"', '"lowPrice"', '"offerPrice"']:
                    m = re.search(field + r'\s*:\s*"?(\d+(?:\.\d+)?)"?', t)
                    if m:
                        p = float(m.group(1))
                        if floor <= p <= 50000:
                            return p
            except:
                continue

        for sel in ['.product-price', '.price', 'span[class*="price"]',
                    '[data-testid="product-price"]']:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── ADIDAS ────────────────────────────────────────────────
    elif platform == "adidas":
        # Adidas India - blocks requests, needs Selenium
        # Uses React, prices in JS

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                t = json.dumps(json.loads(script.string or '{}'))
                m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', t)
                if m:
                    p = float(m.group(1))
                    if floor <= p <= 50000:
                        return p
            except:
                continue

        for sel in ['[class*="gl-price"]', '.gl-price__value',
                    '[class*="price"]', 'span.gl-price']:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── SHOPPERS STOP ─────────────────────────────────────────
    elif platform == "shoppersstop":
        # Traditional website, requests works
        # URLs cleaned of tracking params automatically below

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                t = json.dumps(json.loads(script.string or '{}'))
                m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', t)
                if m:
                    p = float(m.group(1))
                    if floor <= p <= 50000:
                        return p
            except:
                continue

        for sel in ['.pdp-price', '.product-price', 'span[class*="price"]',
                    '.price-final', '.actual-price']:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── MAMAEARTH ─────────────────────────────────────────────
    elif platform == "mamaearth":
        # Shopify-based. Shows USP (unit selling price) like Rs.3.51/ml.
        # Our extract_price with the skincare floor (99) handles this fine.
        # The USP pattern stripper in extract_price removes them first.

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                t = json.dumps(json.loads(script.string or '{}'))
                for field in [r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?',
                              r'"lowPrice"\s*:\s*"?(\d+)"?']:
                    m = re.search(field, t)
                    if m:
                        p = float(m.group(1))
                        if floor <= p <= 50000:
                            return p
            except:
                continue

        for sel in ['.price__current', '.price-item--sale',
                    '.price-item--regular', 'span.product__price',
                    '[class*="product-price"]']:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── D2C BRANDS: Milagro, LA Girl, Off Duty ───────────────
    elif platform in ["milagro", "lagirl", "offduty"]:
        # Small Shopify-based D2C stores. Generally cooperative.
        # Same approach as Mamaearth.

        for script in soup.find_all('script', type='application/ld+json'):
            try:
                t = json.dumps(json.loads(script.string or '{}'))
                m = re.search(r'"price"\s*:\s*"?(\d+(?:\.\d+)?)"?', t)
                if m:
                    p = float(m.group(1))
                    if floor <= p <= 50000:
                        return p
            except:
                continue

        for sel in ['.price__current', '.price-item--sale',
                    '.price-item--regular', '[class*="price"]']:
            el = soup.select_one(sel)
            if el:
                p = extract_price(el.get_text(), floor)
                if p:
                    return p

    # ── GENERIC FALLBACK ──────────────────────────────────────
    # If nothing platform-specific worked, scan ALL elements with
    # "price" in the class name. Last resort but often works.
    if not price:
        for el in soup.find_all(class_=re.compile(r'price', re.I))[:20]:
            p = extract_price(el.get_text(), floor)
            if p:
                return p

    return price


def get_image(soup, platform):
    """Extract product image URL for Streamlit display."""
    try:
        if platform == "myntra":
            img = soup.find('img', class_=re.compile(r'image-grid', re.I))
            if img:
                return img.get('src') or img.get('data-src')
        if platform == "amazon":
            img = soup.find('img', id='landingImage')
            if img:
                return img.get('src')
        # Generic: find first image with 'product' or 'cdn' in src
        for img in soup.find_all('img', src=True):
            src = img.get('src', '')
            if (any(x in src.lower() for x in ['product','item','cdn','upload'])
                    and src.startswith('http')):
                return src
    except:
        pass
    return None


# ═══════════════════════════════════════════════════════════════
# SECTION 8: PLATFORM NORMALIZATION
#
# Your Excel has "Max Fashion", "LA Girl", "Shoppers Stop"
# We need lowercase single-word keys to match the if/elif above.
# This function converts any variation to the right key.
# ═══════════════════════════════════════════════════════════════

PLATFORM_MAP = {
    'max fashion': 'maxfashion',
    'max':         'maxfashion',
    'la girl':     'lagirl',
    'lagirl':      'lagirl',
    'la girl india': 'lagirl',
    'shoppers stop': 'shoppersstop',
    'shoppersstop':  'shoppersstop',
    'off duty':    'offduty',
    'offduty':     'offduty',
    'off duty india': 'offduty',
    'mamaearth':   'mamaearth',
    'milagro':     'milagro',
    'amazon':      'amazon',
    'flipkart':    'flipkart',
    'puma':        'puma',
    'adidas':      'adidas',
    'myntra':      'myntra',
}

def normalize(name):
    return PLATFORM_MAP.get(name.lower().strip(), name.lower().replace(' ',''))


# ═══════════════════════════════════════════════════════════════
# SECTION 9: URL UTILITIES
# ═══════════════════════════════════════════════════════════════

def clean_tracking_params(url):
    """
    Remove Google Ads tracking params from Shoppers Stop URLs.
    ?gclid=CjwK...&utm_source=... -> just the product URL
    These params can cause redirects or different page versions.
    """
    try:
        from urllib.parse import urlparse, parse_qs, urlencode
        parsed = urlparse(url)
        if not parsed.query:
            return url
        # Keep only non-tracking params
        tracking = {'gclid','gbraid','gad_source','gad_campaignid',
                   'utm_source','utm_medium','utm_campaign',
                   'utm_content','utm_term','nsbp'}
        params = parse_qs(parsed.query, keep_blank_values=True)
        clean  = {k: v for k, v in params.items() if k not in tracking}
        new_query = urlencode(clean, doseq=True)
        return parsed._replace(query=new_query).geturl().rstrip('?')
    except:
        return url


def resolve_short_url(url):
    """
    Follow redirect to get real URL.
    dl.flipkart.com/s/XXXX -> actual product page URL

    HOW REDIRECTS WORK:
    dl.flipkart.com/s/rAbjEg is a short link.
    When you open it, server says "go to this longer URL instead".
    That's a redirect. We follow it to get the real product URL.
    requests.head() = ask for headers only (fast), follow_redirects=True
    """
    try:
        resp = requests.head(url, headers=get_headers(),
                            allow_redirects=True, timeout=10)
        if resp.url != url:
            print(f"    Short URL resolved: ...{resp.url[-50:]}")
        return resp.url
    except:
        return url


# ═══════════════════════════════════════════════════════════════
# SECTION 10: REQUESTS-BASED SCRAPER (fast)
#
# WHEN THIS WORKS: Amazon, Shoppers Stop, Puma, D2C brand sites
# WHEN THIS FAILS: Myntra (React), Flipkart (React), Max Fashion
# HOW TO TELL: status=200 but price=None means JS needed
# ═══════════════════════════════════════════════════════════════

def try_requests(url, platform, category):
    """
    Try to get price using simple HTTP request.
    Fast but can't run JavaScript.
    """
    try:
        session = requests.Session()
        headers = get_headers()

        # Visit homepage first for cookies (looks more human)
        # A real user visits homepage before jumping to a product.
        # This also sets session cookies that product pages may check.
        try:
            domain  = urlparse(url).netloc
            scheme  = urlparse(url).scheme
            home    = f"{scheme}://{domain}"
            session.get(home, headers=headers, timeout=8)
            time.sleep(random.uniform(1.5, 3.0))
        except:
            pass

        resp = session.get(url, headers=headers, timeout=15, allow_redirects=True)
        print(f"    status={resp.status_code}", end="")

        # Status code meanings:
        # 200 = success (but might be empty if JS-rendered)
        # 403 = Forbidden (bot detected) -> use Selenium
        # 404 = Page not found -> URL is wrong or product removed
        # 429 = Too many requests -> wait much longer
        # 503 = Server overloaded / blocking -> wait

        if resp.status_code in [429, 503]:
            t = random.uniform(*SLEEP_RATE_LIMITED)
            print(f" RATE_LIMITED - waiting {t:.0f}s")
            time.sleep(t)
            return None, None, resp.status_code

        if resp.status_code == 403:
            print(" BLOCKED")
            return None, None, 403

        if resp.status_code == 404:
            print(" 404 - URL invalid or product removed")
            return None, None, 404

        if resp.status_code != 200:
            print(f" ERROR {resp.status_code}")
            return None, None, resp.status_code

        print()

        soup  = BeautifulSoup(resp.text, 'lxml')
        price = get_price_from_page(soup, platform, category)
        img   = get_image(soup, platform)

        return price, img, 200

    except requests.exceptions.Timeout:
        print(" TIMEOUT")
        return None, None, 0
    except requests.exceptions.ConnectionError:
        print(" CONNECTION_ERROR")
        return None, None, 0
    except Exception as e:
        print(f" ERROR: {str(e)[:40]}")
        return None, None, 0


# ═══════════════════════════════════════════════════════════════
# SECTION 11: SELENIUM-BASED SCRAPER (handles JavaScript)
#
# WHAT SELENIUM DOES:
# Opens a real Chrome browser (invisible/headless mode).
# Visits the URL. Waits for JavaScript to load prices.
# Reads the final HTML. Closes Chrome.
#
# WHY HARDER TO DETECT THAN REQUESTS:
# Because it IS a real browser. JavaScript runs normally.
# The only difference from a human is the 'webdriver' flag
# in JavaScript. We remove that with execute_script().
#
# PLATFORMS THAT NEED SELENIUM:
# Myntra, Flipkart, Max Fashion, Adidas (always)
# Off Duty, sometimes Mamaearth
# ═══════════════════════════════════════════════════════════════

def build_driver():
    """
    Creates a Selenium Chrome driver with all anti-detection settings.
    Called fresh for each scrape (not reused between products).

    WHY NOT REUSE: After scraping 10 sites, the browser has cookies,
    cached data, browsing history. Sites can detect unusual patterns.
    Fresh browser per product = clean slate each time.
    Slower but safer.
    """
    opts = Options()

    # Headless = no visible window. Remove this line to WATCH it scrape.
    # Useful for debugging: you can see exactly what the browser loads.
    opts.add_argument("--headless=new")

    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")

    # This removes the automation detection flag from Chrome.
    # Websites do: if (navigator.webdriver) { block(); }
    # This argument prevents Chrome from setting that flag.
    opts.add_argument("--disable-blink-features=AutomationControlled")

    # Random window size = each "browser" looks slightly different
    w = random.randint(1280, 1920)
    h = random.randint(768, 1080)
    opts.add_argument(f"--window-size={w},{h}")

    # Use a random User-Agent from our pool
    opts.add_argument(f"user-agent={get_headers()['User-Agent']}")

    # Remove Selenium signatures from Chrome's extension list
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)

    # webdriver-manager downloads the right ChromeDriver for your Chrome version
    # You don't need to manually download/update ChromeDriver
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)

    # Remove navigator.webdriver JavaScript property
    # Even though we disabled it at Chrome level, some sites check via JS
    # This double-removes it at the JavaScript level too
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    # Add more human-like browser properties
    # plugins=5 fake plugins, languages=Indian English, window.chrome = exists
    # These are properties a real Chrome browser always has
    # Selenium by default doesn't set them, which looks suspicious
    driver.execute_script("""
        Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3,4,5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-IN','en-US','hi']});
        window.chrome = {runtime: {}};
    """)

    return driver


def try_selenium(url, platform, category):
    """
    Scrape using real Chrome browser.
    Called when requests fails.
    """
    if not SELENIUM_OK:
        print("    Selenium not installed")
        return None, None, 0

    driver = None
    try:
        driver = build_driver()
        driver.get(url)

        # Wait for body to load (page started loading)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Scroll down - real humans scroll. Also triggers lazy-loaded prices.
        driver.execute_script(f"window.scrollTo(0, {random.randint(300, 700)});")

        # Wait for JavaScript to finish loading content
        # 4-7 seconds is realistic for a human reading a page
        time.sleep(random.uniform(4, 7))

        # Get the fully rendered HTML
        soup  = BeautifulSoup(driver.page_source, 'lxml')
        price = get_price_from_page(soup, platform, category)
        img   = get_image(soup, platform)

        return price, img, 200

    except TimeoutException:
        print("    Selenium: page load timeout")
        return None, None, 0
    except Exception as e:
        print(f"    Selenium error: {str(e)[:60]}")
        return None, None, 0
    finally:
        # ALWAYS close browser in finally block
        # finally runs even if there was an error above
        # Without this, Chrome processes accumulate and crash your computer
        if driver:
            try:
                driver.quit()
            except:
                pass


# ═══════════════════════════════════════════════════════════════
# SECTION 12: PLATFORM ROUTING
#
# SMART ROUTING: Some platforms ALWAYS need Selenium.
# No point trying requests first - it wastes time AND looks
# suspicious to the server (a failed request before a Selenium
# request = double traffic = more suspicious).
#
# SELENIUM-FIRST PLATFORMS:
# - Flipkart: requests always gets blocked or empty page
# - Myntra: same (but we try requests for the JSON trick)
# - Adidas: blocks requests with 403
# - Max Fashion: requests gets HTML without prices (JS-rendered)
#
# REQUESTS-FIRST PLATFORMS:
# - Amazon: cooperative, works 95% of the time
# - Shoppers Stop: traditional site, works
# - Puma: works with requests
# - D2C brands (Mamaearth etc): usually works
# ═══════════════════════════════════════════════════════════════

SELENIUM_FIRST_PLATFORMS = {'flipkart', 'adidas', 'maxfashion'}
# For these, we skip requests entirely and go straight to Selenium.
# Myntra is NOT in this set because the JSON trick sometimes works.


def scrape_one(name, url, platform, category):
    """
    Scrape price for one product on one platform.
    Tries requests first (unless Selenium-first platform),
    then falls back to Selenium.

    Returns: (price, image_url, method, status_code)
    """
    print(f"\n  [{platform.upper()}] {name[:55]}")
    print(f"  {url[:72]}...")

    # Pre-process URL based on platform
    actual_url = url

    if 'dl.flipkart.com' in url or 'fkrt.it' in url:
        print(f"  Resolving short URL...")
        actual_url = resolve_short_url(url)

    if 'shoppersstop.com' in url:
        cleaned = clean_tracking_params(url)
        if cleaned != url:
            print(f"  Removed tracking params")
            actual_url = cleaned

    # Check for known-bad URL patterns
    if 'hyperlocal' in url.lower():
        print(f"  SKIP: hyperlocal URL is not a product page")
        print(f"  Fix: replace this URL in your Excel file")
        return None, None, "bad_url", 0

    # SELENIUM-FIRST: skip requests entirely for these platforms
    if platform in SELENIUM_FIRST_PLATFORMS:
        print(f"  Going direct to Selenium (requests always fails for {platform})")
        price, img, status = try_selenium(actual_url, platform, category)
        if price:
            print(f"  Selenium OK -> Rs.{price:,.0f}")
            return price, img, "selenium", status
        print(f"  FAILED")
        return None, None, "failed", status

    # REQUESTS FIRST for all other platforms
    price, img, status = try_requests(actual_url, platform, category)

    if price:
        print(f"  requests OK -> Rs.{price:,.0f}")
        return price, img, "requests", status

    print(f"  requests failed -> Selenium...")
    time.sleep(random.uniform(2, 4))

    price, img, status = try_selenium(actual_url, platform, category)

    if price:
        print(f"  Selenium OK -> Rs.{price:,.0f}")
        return price, img, "selenium", status

    print(f"  BOTH FAILED")
    return None, None, "failed", status


# ═══════════════════════════════════════════════════════════════
# SECTION 13: RESULT VALIDATION
#
# Even after all the extraction work, we do a sanity check.
# If a price passes all the technical filters but is still
# clearly wrong (like a Rs.150 shirt), we flag it as suspicious.
# We don't delete it - we flag it so you can review it.
# The CSV keeps the data, but adds a 'suspicious' column.
# ═══════════════════════════════════════════════════════════════

def validate_pair(myntra_price, comp_price, category):
    """
    Check if a price pair makes sense.
    Returns (is_valid, flag_reason)
    """
    if not myntra_price or not comp_price:
        return False, "missing_price"

    floor = get_floor(category)

    if comp_price < floor:
        return False, f"comp_price_below_floor_{floor}"

    if myntra_price < floor:
        return False, f"myntra_price_below_floor_{floor}"

    # If delta is more than 300% either direction, something is probably wrong
    # Exception: legitimate sales can create large deltas
    delta_pct = abs((myntra_price - comp_price) / comp_price * 100)
    if delta_pct > 500:
        return False, f"delta_too_large_{delta_pct:.0f}pct"

    return True, "ok"


# ═══════════════════════════════════════════════════════════════
# SECTION 14: MAIN DAILY RUN
# ═══════════════════════════════════════════════════════════════

def run(input_file="products_urls_project.xlsx"):
    """
    Run the full scrape for all products.
    Call this once per day (or twice max, different IP each time).

    APPENDING LOGIC:
    This function ALWAYS appends to data/price_parity_raw.csv.
    It never overwrites. Each row has scrape_date + scrape_time.
    To separate days in analysis: df[df['scrape_date'] == 'YYYY-MM-DD']
    """
    today = date.today().isoformat()
    now   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"\n{'='*62}")
    print(f"PROJECT SIPHON PRICE SCRAPER v4")
    print(f"Run: {now}")
    print(f"Sleep: {SLEEP_BETWEEN_PLATFORMS} between platforms")
    print(f"Sleep: {SLEEP_BETWEEN_PRODUCTS} between products")
    print(f"Selenium-first: {SELENIUM_FIRST_PLATFORMS}")
    print(f"{'='*62}")

    # Load Excel
    try:
        df = pd.read_excel(input_file)
        df.columns = [c.strip().lower().replace(' ','_') for c in df.columns]
        print(f"\nLoaded: {len(df)} products")
        print(f"Platforms: {df['competitor_name'].value_counts().to_dict()}")
    except FileNotFoundError:
        print(f"ERROR: {input_file} not found.")
        print(f"Ensure Excel file and this script are in same folder.")
        return

    # Check required columns
    required = ['product_name','myntra_url','competitor_url','competitor_name','category']
    missing  = [c for c in required if c not in df.columns]
    if missing:
        print(f"ERROR: Missing columns: {missing}")
        print(f"Found columns: {list(df.columns)}")
        return

    output   = "data/price_parity_raw.csv"
    results  = []
    failed   = []
    skipped  = []
    flagged  = []

    for idx, row in df.iterrows():
        name     = str(row['product_name']).strip()
        m_url    = str(row['myntra_url']).strip()
        c_url    = str(row['competitor_url']).strip()
        comp_raw = str(row['competitor_name']).strip()
        comp     = normalize(comp_raw)
        cat      = str(row['category']).strip()

        print(f"\n[{idx+1}/{len(df)}] {name[:62]}")
        print(f"Category: {cat} | Competitor: {comp_raw} | Floor: Rs.{get_floor(cat)}")
        print("-" * 62)

        # Scrape Myntra
        m_price, m_img, m_meth, m_stat = scrape_one(name, m_url, "myntra", cat)

        # Wait between platforms
        t = random.uniform(*SLEEP_BETWEEN_PLATFORMS)
        print(f"\n  sleeping {t:.1f}s between platforms...")
        time.sleep(t)

        # Scrape competitor
        c_price, c_img, c_meth, c_stat = scrape_one(name, c_url, comp, cat)

        # Calculate metrics
        delta = delta_pct = parity = None
        is_valid, flag_reason = validate_pair(m_price, c_price, cat)

        if is_valid:
            delta     = round(m_price - c_price, 2)
            delta_pct = round((delta / c_price) * 100, 2)
            if   abs(delta_pct) <= 10:  parity = "parity"
            elif delta_pct > 10:        parity = "myntra_higher"
            else:                       parity = "myntra_lower"
            print(f"\n  Rs.{m_price:,.0f} vs {comp_raw} Rs.{c_price:,.0f} | {delta_pct:+.1f}% | {parity}")

        elif m_price and c_price:
            # Prices scraped but flagged as suspicious
            delta     = round(m_price - c_price, 2)
            delta_pct = round((delta / c_price) * 100, 2)
            parity    = "FLAGGED"
            flagged.append(f"{name} ({flag_reason})")
            print(f"\n  FLAGGED: Rs.{m_price:,.0f} vs Rs.{c_price:,.0f} | {flag_reason}")

        elif m_meth == "bad_url" or c_meth == "bad_url":
            skipped.append(f"{name} (bad URL)")
        else:
            failed.append(name)

        results.append({
            "scrape_date":          today,
            "scrape_time":          now,
            "product_name":         name,
            "category":             cat,
            "competitor_platform":  comp_raw,
            "myntra_price":         m_price,
            "competitor_price":     c_price,
            "price_delta":          delta,
            "price_delta_pct":      delta_pct,
            "parity_flag":          parity,
            "data_quality":         flag_reason if not is_valid and m_price else "ok",
            "myntra_img_url":       m_img,
            "competitor_img_url":   c_img,
            "myntra_url":           m_url,
            "competitor_url":       c_url,
            "myntra_method":        m_meth,
            "comp_method":          c_meth,
            "myntra_status":        m_stat,
            "comp_status":          c_stat,
            "floor_used":           get_floor(cat),
        })

        # Wait between products
        if idx < len(df) - 1:
            t = random.uniform(*SLEEP_BETWEEN_PRODUCTS)
            print(f"\n  sleeping {t:.1f}s before next product...")
            time.sleep(t)

    # Save (always append)
    rdf = pd.DataFrame(results)
    if os.path.exists(output):
        existing = pd.read_csv(output)
        combined = pd.concat([existing, rdf], ignore_index=True)
        combined.to_csv(output, index=False)
        print(f"\nAppended -> {output} | Total rows: {len(combined)}")
    else:
        rdf.to_csv(output, index=False)
        print(f"\nCreated -> {output} | Rows: {len(rdf)}")

    # Summary
    ok = rdf[rdf['parity_flag'].isin(['parity','myntra_higher','myntra_lower'])]

    print(f"\n{'='*62}")
    print(f"SUMMARY — {today}")
    print(f"{'='*62}")
    print(f"Total:    {len(rdf)}")
    print(f"Valid:    {len(ok)}")
    print(f"Flagged:  {len(flagged)}")
    print(f"Failed:   {len(failed)}")
    print(f"Skipped:  {len(skipped)}")

    if len(ok) >= 10:
        at_par = (ok['parity_flag'] == 'parity').sum()
        m_hi   = (ok['parity_flag'] == 'myntra_higher').sum()
        m_lo   = (ok['parity_flag'] == 'myntra_lower').sum()
        med    = ok['price_delta_pct'].median()

        print(f"\nParity:")
        print(f"  At parity (<=10%) : {at_par} ({at_par/len(ok)*100:.0f}%)")
        print(f"  Myntra higher     : {m_hi}")
        print(f"  Myntra lower      : {m_lo}")
        print(f"\nMedian delta: {med:+.1f}%  <- USE THIS for Wilcoxon")
        print(f"(Mean is skewed by outliers - ignore it)")

    if flagged:
        print(f"\nFlagged (suspicious prices - review in CSV):")
        for f in flagged:
            print(f"  ! {f}")

    if failed:
        print(f"\nFailed (fix selectors and rerun):")
        for f in failed:
            print(f"  x {f}")
        print(f"\nFIX: Open URL in Chrome, F12, right-click price,")
        print(f"Inspect, note class name, update get_price_from_page()")

    # Log
    med_str = f"{ok['price_delta_pct'].median():+.1f}%" if len(ok) > 0 else "N/A"
    with open("data/scrape_log.txt", "a", encoding="utf-8") as f:
        f.write(f"\n{now} | valid={len(ok)}/{len(rdf)} | median={med_str} | flagged={len(flagged)} | failed={len(failed)}\n")
        for x in flagged: f.write(f"  FLAGGED: {x}\n")
        for x in failed:  f.write(f"  FAILED: {x}\n")

    print(f"\nLog -> data/scrape_log.txt")
    print(f"Run again tomorrow (different IP) for Next Day.\n")
    return rdf


if __name__ == "__main__":
    run()