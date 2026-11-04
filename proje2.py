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

# ==============================================================================
# 5. STATE & NOTIFICATION DISPATCH (Week 4, Slide 18, 30, 36, 38, 42)
# ==============================================================================

def load_saved_state(filepath):
    """Load stored state from JSON file (Week 4, Slide 36)."""
    if not os.path.exists(filepath):
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(filepath, state_dict):
    """Persist updated state into JSON file (Week 4, Slide 36)."""
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state_dict, f, indent=2, ensure_ascii=False)


def format_istanbul_time():
    """Convert UTC to Europe/Istanbul timezone string (Week 4, Slide 28 & 30)."""
    now_utc = datetime.now(timezone.utc)
    return now_utc.astimezone(ZoneInfo("Europe/Istanbul")).strftime("%d %b %H:%M %z")


def send_telegram_message(message_text, bot_token, chat_id):
    """Publish notification via Telegram Bot API POST (Week 4, Slide 42)."""
    if not bot_token or not chat_id:
        print("\n[UYARI] Bot Token veya Chat ID eksik! Mesaj gönderilmedi.\n")
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": str(chat_id).strip(),
        "text": message_text,
        "parse_mode": "Markdown"
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        print(f"\n📡 Telegram API İsteği Yapıldı -> Durum: {r.status_code}")
        if r.status_code != 200:
            print(f"Ayrıntı: {r.text}\n")
        r.raise_for_status()
        print("✅ Telegram bildirimi başarıyla teslim edildi!\n")
        return True
    except requests.RequestException as error:
        print(f"❌ Telegram gönderim hatası: {error}\n")
        return False


def dispatch_daily_menu(daily_menu, bot_token, chat_id):
    """Sends the daily 4-course menu as an actionable morning card."""
    time_str = format_istanbul_time()
    lines = [f"🍽️ *TODAY'S 4-COURSE MENU* 📅\n_{time_str}_\n"]
    for course, item in daily_menu.items():
        lines.append(f"• *{course}:* [{item['title']}]({item['url']})")

    lines.append("\n💡 _All ingredients are being scanned in live markets for price drops!_")
    return send_telegram_message("\n".join(lines), bot_token, chat_id)


def dispatch_price_alerts(price_drops, bot_token, chat_id):
    """
    Intelligent Batching Alert:
    - If 1 drop: Sends immediate focused alert.
    - If >=2 drops: Consolidates into 1 clean digest so user isn't spammed!
    (Week 4, Slide 37, 53 & 56).
    """
    if not price_drops:
        return True

    time_str = format_istanbul_time()

    if len(price_drops) == 1:
        d = price_drops[0]
        recipes_text = ", ".join(d["matched_recipes"]) if d["matched_recipes"] else "Pantry Essential"
        msg = (
            f"🔔 *PRICE DROP ALERT!* 📉\n"
            f"• Ingredient: *{d['ingredient'].capitalize()}*\n"
            f"• Product: {d['product']}\n"
            f"• Old Price: ~{d['old_price']:.2f} {d['currency']}~\n"
            f"• *New Price: {d['new_price']:.2f} {d['currency']}*\n"
            f"• Savings: *{d['saved']:.2f} {d['currency']}*\n\n"
            f"🍲 *Recipes you can cook:*\n↳ {recipes_text}\n\n"
            f"🕒 Time: {time_str} (Istanbul)"
        )
    else:
        # Consolidated batch digest
        item_lines = []
        for d in price_drops:
            recipes_text = ", ".join(d["matched_recipes"][:2]) if d["matched_recipes"] else "Pantry"
            item_lines.append(
                f"🔻 *{d['ingredient'].capitalize()}*: ~{d['old_price']:.2f}~ ➡️ *{d['new_price']:.2f} {d['currency']}* "
                f"(Saved: {d['saved']:.2f} {d['currency']})\n"
                f"   ↳ Related: _{recipes_text}_"
            )
        msg = (
            f"🛒 *BATCHED PRICE DROP DIGEST ({len(price_drops)} Items)* 📉\n"
            f"Multiple tracked ingredients dropped in price simultaneously!\n\n"
            + "\n\n".join(item_lines) +
            f"\n\n🕒 Time: {time_str} (Istanbul)"
        )

    return send_telegram_message(msg, bot_token, chat_id)


# ==============================================================================
# 6. SCAN PIPELINE & MAIN WORKFLOW
# ==============================================================================

def run_monitoring_round(args, daily_menu, recipe_book, all_groceries):
    """Executes one scan cycle: API fetch -> compare state -> dispatch alerts."""
    start_counter = perf_counter()
    print(f"\nScanning prices for {len(all_groceries)} ingredients across Open Food Facts...")

    all_current_prices = []
    # Test top 6 ingredients for responsive execution
    for ing in list(all_groceries)[:6]:
        records = fetch_ingredient_prices(ing)
        if records:
            all_current_prices.extend(records)

    if not all_current_prices:
        print("No price data retrieved. Existing state preserved.")
        return

    saved_state = load_saved_state(STATE_FILE)
    price_drops = []
    updated_state = dict(saved_state)

    for record in all_current_prices:
        rec_id = record["id"]
        curr_price = record["price"]
        ing_name = record["ingredient"]

        related = find_recipes_for_ingredient(recipe_book, daily_menu, ing_name)

        if rec_id in saved_state:
            prev_price = saved_state[rec_id]["price"]
            diff = curr_price - prev_price
            if diff < 0:
                price_drops.append({
                    "ingredient": ing_name,
                    "product": record["product_name"],
                    "old_price": prev_price,
                    "new_price": curr_price,
                    "saved": abs(diff),
                    "currency": record["currency"],
                    "matched_recipes": related
                })

        updated_state[rec_id] = {
            "product_name": record["product_name"],
            "ingredient": ing_name,
            "price": curr_price,
            "currency": record["currency"]
        }

    # Dispatch alerts (single or batched)
    if price_drops:
        dispatch_price_alerts(price_drops, args.bot_token, args.chat_id)
    else:
        print("Prices checked; no drops observed.")

    save_state(STATE_FILE, updated_state)
    elapsed = perf_counter() - start_counter
    print(f"Cycle completed in {elapsed:.4f} seconds. (Drops detected: {len(price_drops)})")


def main():
    """CLI Argument parser and scheduler loop (Week 3, Slide 29; Week 4, Slide 33 & 58)."""
    parser = argparse.ArgumentParser(description="Smart Recipe 4-Course Menu & Price Monitor")
    parser.add_argument("--recipes-dir", default=RECIPES_DIR, help="Path to local recipe folder")
    parser.add_argument("--bot-token", default=DEFAULT_BOT_TOKEN, help="Telegram Bot Token")
    parser.add_argument("--chat-id", default=DEFAULT_CHAT_ID, help="Telegram Chat ID")
    parser.add_argument("--interval", type=int, default=0, help="Monitor interval in seconds (0 for single run)")
    parser.add_argument("--send-menu", action="store_true", help="Dispatch daily 4-course menu at start")
    parser.add_argument("--verbose", action="store_true", help="Print detailed runtime debug logs")
    args = parser.parse_args()

    # Step 1: Load local recipes (preserving Project 1 files)
    recipe_book = load_local_recipes(args.recipes_dir)

    # Step 2: Generate 4-Course Daily Menu from TheMealDB
    daily_menu, menu_groceries = generate_daily_4course_menu()
    save_state(DAILY_MENU_FILE, daily_menu)

    # Step 3: Web Scraping demonstration on a dynamic live recipe URL
    first_meal = list(daily_menu.values())[0]
    scraped_title = scrape_recipe_page(first_meal["url"])
    if args.verbose:
        print(f"Scraped recipe heading via BeautifulSoup: {scraped_title}")

    # Combine local ingredients with today's menu ingredients
    all_target_groceries = set(menu_groceries)
    for ings in recipe_book.values():
        all_target_groceries.update(ings)

    # Send morning menu if requested or on first single run
    if args.send_menu or args.interval <= 0:
        dispatch_daily_menu(daily_menu, args.bot_token, args.chat_id)

    # Step 4: Run Monitor (Single run or Overlap-Guarded scheduler loop)
    if args.interval <= 0:
        run_monitoring_round(args, daily_menu, recipe_book, all_target_groceries)
    else:
        is_busy = False
        print(f"\nMonitoring active: checking prices every {args.interval}s. Press Ctrl+C to stop.")
        while True:
            if not is_busy:
                is_busy = True
                run_monitoring_round(args, daily_menu, recipe_book, all_target_groceries)
                is_busy = False
            else:
                print("Previous scan still in progress. Skipping overlap.")
            time.sleep(args.interval)


if __name__ == "__main__":
    main()