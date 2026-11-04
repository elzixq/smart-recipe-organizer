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
# ==============================================================================
# 2. THEMEALDB & WEB SCRAPING MODULE 
# ==============================================================================

def fetch_meal_details(meal_id):
    """Fetch meal details and ingredients using lookup endpoint."""
    try:
        url = f"{THEMEALDB_LOOKUP_URL}?i={meal_id}"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = json.loads(resp.text)
        meals = data.get("meals")
        if not meals:
            return None

        m = meals[0]
        title = clean_whitespace(m.get("strMeal", "Daily Meal"))
        ingredients = set()
        for i in range(1, 21):
            ing = m.get(f"strIngredient{i}")
            if ing and ing.strip():
                clean_ing = clean_whitespace(ing).lower()
                token = clean_ing.split()[-1].strip(".,;:-")
                if token:
                    ingredients.add(token)

        return {
            "id": meal_id,
            "title": title,
            "url": f"https://www.themealdb.com/meal/{meal_id}",
            "ingredients": list(ingredients)
        }
    except requests.RequestException as error:
        print(f"Error fetching meal {meal_id}: {error}")
        return None


def generate_daily_4course_menu():
    """
    Selects 1 Breakfast, 1 Starter/Soup, 1 Main, and 1 Dessert from TheMealDB.
    Returns the menu dict and the set of ingredients needed for today.
    """
    print("🍳 Fetching today's 4-course menu from TheMealDB...")
    daily_menu = {}
    today_groceries = set()

    for course_name, api_category in MENU_CATEGORIES.items():
        try:
            url = f"{THEMEALDB_FILTER_URL}?c={api_category}"
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            data = json.loads(resp.text)
            meals = data.get("meals", [])

            if meals:
                selected_meal = meals[0]
                meal_id = selected_meal.get("idMeal")
                details = fetch_meal_details(meal_id)
                if details:
                    daily_menu[course_name] = details
                    today_groceries.update(details["ingredients"])
                    time.sleep(0.2)
                    continue

            # Fallback data if category is empty
            daily_menu[course_name] = {
                "id": f"FALLBACK_{course_name}",
                "title": f"Classic {course_name}",
                "url": "https://www.themealdb.com",
                "ingredients": ["egg", "milk", "tomato"]
            }
        except requests.RequestException:
            # Fallback if connection fails
            daily_menu[course_name] = {
                "id": f"DEFAULT_{course_name}",
                "title": f"Traditional {course_name}",
                "url": "https://www.themealdb.com",
                "ingredients": ["bread", "cheese", "tea"]
            }

    return daily_menu, today_groceries


def scrape_recipe_page(recipe_url):
    """
    Demonstrates BeautifulSoup HTML extraction directly from a recipe page URL (Week 4, Slide 10-14).
    """
    try:
        resp = requests.get(recipe_url, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        heading = soup.select_one("h1") or soup.select_one("h2")
        title = clean_whitespace(heading.get_text()) if heading else "Recipe Details"
        return title
    except requests.RequestException:
        return "TheMealDB Recipe Page"
# ==============================================================================
# 3. LOCAL RECIPES & MATCHING ENGINE 
# ==============================================================================

def load_local_recipes(recipes_folder):
    """
    Reads existing .txt recipe files so newly scraped items don't delete them.
    (Week 2, Slide 24-28).
    """
    recipe_book = {
        "Pancakes": {"flour", "milk", "egg", "butter"},
        "Chicken Rice": {"chicken", "rice", "onion"},
        "Tomato Soup": {"tomato", "butter", "flour"}
    }
    if not os.path.isdir(recipes_folder):
        return recipe_book

    for filename in sorted(os.listdir(recipes_folder)):
        filepath = os.path.join(recipes_folder, filename)
        if not os.path.isfile(filepath):
            continue

        recipe_name = os.path.splitext(filename)[0]
        ingredients = set()

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                clean_line = line.strip().lower()
                if clean_line.startswith("ingredient:") or clean_line.startswith("-"):
                    parts = clean_line.replace("ingredient:", "").replace("-", "").strip()
                    if parts:
                        token = parts.split()[0].strip(".,;")
                        ingredients.add(token)

        if ingredients:
            recipe_book[recipe_name] = ingredients

    return recipe_book


def find_recipes_for_ingredient(recipe_book, daily_menu, ingredient_name):
    """Finds which local recipes or daily menu items use this discounted ingredient."""
    matched = []
    ing_lower = ingredient_name.lower()

    # Search in daily menu items
    for course, item in daily_menu.items():
        if any(ing_lower in x or x in ing_lower for x in item.get("ingredients", [])):
            matched.append(f"{course}: {item['title']}")

    # Search in local recipes
    for r_name, ings in recipe_book.items():
        if any(ing_lower in x or x in ing_lower for x in ings):
            matched.append(f"Local Recipe: {r_name}")

    return matched
# ==============================================================================
# 4. OPEN FOOD FACTS API FETCH & RETRIES 
# ==============================================================================

def fetch_with_retry(url, max_attempts=3):
    """Transient failure retry with 1s, then 2s backoff (Week 4, Slide 5 & 34)."""
    wait_sec = 1
    for attempt in range(1, max_attempts + 1):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code in (401, 403):
                print(f"Access denied ({resp.status_code}). Stopping.")
                return None
            resp.raise_for_status()
            return resp.text
        except requests.RequestException as error:
            print(f"Attempt {attempt} failed: {error}")
            if attempt < max_attempts:
                print(f"Waiting {wait_sec}s before retry...")
                time.sleep(wait_sec)
                wait_sec *= 2
    return None


def fetch_ingredient_prices(ingredient_name):
    """Query Open Food Facts Prices API using urlencode (Week 4, Slide 6 & 20)."""
    query = urlencode({"product_name__like": ingredient_name.lower().strip(), "size": 3})
    full_url = f"{PRICES_API_URL}?{query}"

    raw_json = fetch_with_retry(full_url)
    if raw_json is None:
        return []

    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError:
        return []

    items = data.get("items")
    if not items:
        return []

    valid_records = []
    for item in items:
        rec_id = str(item.get("id", "")).strip()
        product = item.get("product") or {}
        p_name = product.get("product_name") or ingredient_name
        currency = item.get("currency") or "EUR"
        price_val = item.get("price")

        record = {
            "id": f"OFF_{rec_id}",
            "ingredient": ingredient_name,
            "product_name": clean_whitespace(p_name),
            "price": float(price_val) if price_val is not None else None,
            "currency": currency
        }

        if validate_price_record(record):
            valid_records.append(record)

    return deduplicate_records_by_id(valid_records)