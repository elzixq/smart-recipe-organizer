# Smart Recipe Organizer & Kitchen Assistant

A Python-based project developed in two consecutive phases to simplify recipe management, kitchen inventory tracking, ingredient matching, and grocery price monitoring.

The project combines local recipe organization with external API integrations, web scraping, automated price comparison, and Telegram notifications.

## Project Overview

This project consists of two complementary development phases:

- **Phase 1 – Recipe Organizer (`app3.py`):** Focuses on organizing local recipe files, managing kitchen inventory, matching available ingredients with recipes, and providing interactive cooking assistance.
- **Phase 2 – Recipe & Price Monitor (`proje2.py`):** Extends the project with external recipe APIs, ingredient extraction, grocery price monitoring, and automated Telegram notifications.

Together, these phases create a kitchen assistant that connects recipe management with ingredient availability and grocery price awareness.

---

## Phase 1 – Recipe Organizer

The first phase focuses on local recipe management and kitchen inventory organization.

### Features

- **Automatic File Organization:** Categorizes `.txt` recipe files based on their filename prefixes:
  - `breakfast_` → `Breakfast_Recipes/`
  - `main_` → `Main_Course_Recipes/`
  - `dessert_` → `Dessert_Recipes/`
- **Dry-Run Safety Mode:** Simulates file movements without modifying the filesystem using `--dry-run`.
- **Ingredient Matching:** Compares available kitchen inventory with recipe requirements.
- **Missing Ingredient Detection:** Identifies ingredients that are not currently available.
- **Interactive Cooking Assistant:** Displays step-by-step cooking instructions with exact measurements.

### Main Components

| Component | Description |
|---|---|
| `app3.py` | Main CLI application for file organization and recipe queries |
| `ingredients.txt` | Kitchen inventory, with available ingredients listed line by line |
| `Breakfast_Recipes/` | Stores breakfast recipes |
| `Main_Course_Recipes/` | Stores main course recipes |
| `Dessert_Recipes/` | Stores dessert recipes |
| `contributions/` | Contains contribution reports for team members |

### Usage

Run the application:

```bash
python app3.py
```

Preview file organization without moving files:

```bash
python app3.py --dry-run
```

---

## Phase 2 – Recipe & Price Monitor

The second phase expands the application by integrating external APIs and automated grocery price monitoring.

### Features

- **Recipe Retrieval:** Fetches recipes from TheMealDB API.
- **Daily Menu Generation:** Creates a four-course daily menu.
- **Web Scraping:** Uses BeautifulSoup to extract recipe page titles from HTML.
- **Ingredient Collection:** Retrieves ingredients from recipe details and combines them with local recipe data.
- **Grocery Price Retrieval:** Searches for ingredient-related products using the Open Food Facts API.
- **Data Validation:** Validates product records and removes duplicate product IDs.
- **Price Comparison:** Compares current product prices with previously saved prices.
- **Price Drop Detection:** Identifies price decreases and calculates potential savings.
- **Telegram Notifications:** Sends individual or grouped notifications when price drops are detected.
- **Persistent Storage:** Saves price information in a local JSON file.
- **Periodic Monitoring:** Supports repeated price-checking intervals.

### Technologies Used

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Requests | Sending HTTP requests |
| BeautifulSoup | Extracting information from HTML |
| JSON | Storing and processing data |
| TheMealDB API | Retrieving recipes and ingredients |
| Open Food Facts API | Retrieving product prices |
| Telegram Bot API | Sending notifications |
| argparse | Handling command-line arguments |

### How It Works

1. **Recipe Retrieval:** The application retrieves meal categories and recipe information from TheMealDB API.
2. **Recipe Scraping:** BeautifulSoup extracts recipe page titles from HTML content.
3. **Ingredient Collection:** Ingredients are collected from recipe details and combined with local recipe data.
4. **Price Retrieval:** The application searches for ingredient-related products using the Open Food Facts API.
5. **Data Processing:** Retrieved records are validated and duplicate product IDs are removed.
6. **Price Monitoring:** Current prices are compared with previously saved prices.
7. **Notifications:** Telegram notifications are generated when a price decrease is detected.
8. **State Management:** Updated prices are stored in a JSON file for future comparisons.

### Price Monitoring Logic

Products are identified using their unique product IDs.

When a product has been monitored before, its current price is compared with its previously saved price:

```python
diff = curr_price - prev_price

if diff < 0:
    price_drop = abs(diff)
```

If the difference is negative, a price decrease is detected. The application calculates the potential savings and prepares a notification.

The latest price information is then saved in `saved_prices_state.json`.

### Error Handling

The application includes several error-handling mechanisms:

- HTTP request timeouts.
- HTTP status validation.
- Retry mechanism with exponential backoff.
- Handling of request exceptions.
- JSON loading error handling.
- Product record validation.
- Duplicate record removal.

### Usage

Run the application:

```bash
python proje2.py
```

Run periodic price monitoring every hour:

```bash
python proje2.py --interval 3600
```

Specify a custom recipes directory:

```bash
python proje2.py --recipes-dir recipes
```

Enable verbose output:

```bash
python proje2.py --verbose
```

Send the daily menu through Telegram:

```bash
python proje2.py --send-menu
```

### Telegram Configuration (Optional)

Telegram notifications require a bot token and chat ID.

You can provide them using environment variables:

```bash
export BOT_TOKEN="your_bot_token"
export CHAT_ID="your_chat_id"
```

Alternatively, you can provide them as command-line arguments.

---

## Project Structure

```text
Smart-Recipe-Organizer/
│
├── app3.py
├── proje2.py
│
├── ingredients.txt
│
├── Breakfast_Recipes/
├── Main_Course_Recipes/
├── Dessert_Recipes/
│
├── recipes/
│
├── contributions/
│
├── saved_prices_state.json
├── today_menu.json
│
└── README.md
```

### File Descriptions

| File / Directory | Description |
|---|---|
| `app3.py` | First-phase CLI application for recipe organization |
| `proje2.py` | Second-phase application for recipe retrieval and price monitoring |
| `ingredients.txt` | Available kitchen ingredients |
| `Breakfast_Recipes/` | Breakfast recipe collection |
| `Main_Course_Recipes/` | Main course recipe collection |
| `Dessert_Recipes/` | Dessert recipe collection |
| `recipes/` | Local recipe files used by the second phase |
| `contributions/` | Team contribution reports |
| `saved_prices_state.json` | Stores previously monitored product prices |
| `today_menu.json` | Stores the generated daily menu |

---

## Installation

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Smart-Recipe-Organizer
```

### 2. Install Dependencies

For the second phase, install the required Python libraries:

```bash
pip install requests beautifulsoup4
```

The first phase uses Python's built-in libraries for its described CLI and file-management functionality.

**Recommended Python Version:** Python 3.9 or newer.

---

## Current Limitations

- Price monitoring currently checks only the first six ingredients.
- The application stores the latest price rather than a complete historical price series.
- Recipe selection uses the first available API result.
- Ingredient matching uses partial string comparison, which may sometimes produce inaccurate matches.
- Telegram notifications require valid bot credentials for actual delivery.
- The two phases are separate executable scripts and are run independently.

## Future Improvements

- Integrate both phases into a unified command-line interface.
- Connect kitchen inventory directly to the price-monitoring workflow.
- Monitor all ingredients instead of limiting the number to six.
- Store historical price data and visualize price trends.
- Improve ingredient normalization and matching accuracy.
- Add additional recipe and grocery data sources.
- Implement asynchronous requests for improved performance.
- Develop a graphical user interface.
- Add automated tests for core functionalities.

---