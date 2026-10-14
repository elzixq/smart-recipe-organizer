# smart-recipe-organizer
# Smart Recipe Organizer & Kitchen Assistant

A CLI-based automation tool that categorizes recipe files into designated folders and suggests meals based on available kitchen inventory.

## Project Structure

- `app3.py`: Main executable CLI script handling file organization and interactive recipe queries.
- `ingredients.txt`: Inventory file containing available ingredients line-by-line.
- `Breakfast_Recipes/`: Directory storing organized breakfast recipe files.
- `Main_Course_Recipes/`: Directory storing organized main course recipe files.
- `Dessert_Recipes/`: Directory storing organized dessert recipe files.
- `contributions/`: Directory containing contribution reports for team members.

## Features

- **Automatic File Organization:** Categorizes `.txt` recipes starting with `breakfast_`, `main_`, or `dessert_` into their respective folders.
- **Dry-Run Safety Mode:** Simulates file movements without modifying the filesystem using `--dry-run`.
- **Ingredient Matching:** Compares inventory against recipe requirements and highlights missing items.
- **Interactive Assistant:** Displays step-by-step cooking instructions with exact measurements.

## Usage

### 1. Simulation Mode (Dry-Run)
Preview file movements safely:
```bash
python app3.py --dry-run
