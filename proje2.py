"""
Smart Recipe Organizer - Project 2: Web Recipe & Price Monitor
Authors: COE203 Students
Features:
1. Daily 4-Course Menu (Soup, Breakfast, Main, Dessert) fetched dynamically from TheMealDB.
 2. Web Scraping & API integration (BeautifulSoup + Requests).
3. Open Food Facts Prices API: monitors prices of recipe ingredients.
4. Smart Alert Engine: Immediate single alert or consolidated batch alerts on multi-drops.
5. Telegram Actionable Notifications with direct hardcoded fallback credentials.
"""

import argparse
import json
import os
import time
from time import perf_counter
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from urllib.parse import urlencode
import requests
from bs4 import BeautifulSoup

# Module-level constants
STATE_FILE = "saved_prices_state.json"
DAILY_MENU_FILE = "today_menu.json"
RECIPES_DIR = "recipes"
PRICES_API_URL = "https://prices.openfoodfacts.org/api/v1/prices"
THEMEALDB_FILTER_URL = "https://www.themealdb.com/api/json/v1/1/filter.php"
THEMEALDB_LOOKUP_URL = "https://www.themealdb.com/api/json/v1/1/lookup.php"

DEFAULT_BOT_TOKEN = "9007297052:AAGx-yNP5ZZHw1BlCbqbpnLyVIyQ5utagqA"
DEFAULT_CHAT_ID = "6670809792"

# Categories mapped for the daily 4-course menu 
MENU_CATEGORIES = {
    "Breakfast": "Breakfast",
    "Starter/Soup": "Starter",
    "Main Course": "Chicken",
    "Dessert": "Dessert"
}


# ==============================================================================
# 1. STRING & DATA VALIDATION HELPERS 
# ==============================================================================

def clean_whitespace(raw_text):
    """Whitespace cleanup pipeline (Week 4, Slide 13)."""
    if not raw_text:
        return ""
    return " ".join(str(raw_text).strip().split())


def validate_price_record(record):
    """Validate required fields before trusting the record (Week 4, Slide 17)."""
    item_id = str(record.get("id", "")).strip()
    product_name = clean_whitespace(record.get("product_name", ""))
    price = record.get("price")

    if not item_id or not product_name:
        return False
    if price is None or not isinstance(price, (int, float)) or price <= 0:
        return False
    return True


def deduplicate_records_by_id(records):
    """Keep one record per ID using a dictionary (Week 4, Slide 24)."""
    by_id = {}
    for record in records:
        by_id[record["id"]] = record
    return list(by_id.values())