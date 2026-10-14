import argparse
import os
import shutil

CATEGORIES = {
    "breakfast": "Breakfast_Recipes",
    "main": "Main_Course_Recipes",
    "dessert": "Dessert_Recipes",
}


def get_category(filename):
    clean_name = filename.strip().lower()

    for keyword, folder in CATEGORIES.items():
        if clean_name.startswith((f"{keyword}_", f"{keyword}-", f"{keyword} ")):
            return folder
    return None
def organize_files(target_dir=".", dry_run=False):
    print("=" * 45)
    print("  SMART RECIPE ORGANIZER & KITCHEN ASSISTANT  ")
    print("=" * 45)

    stats = {folder: 0 for folder in CATEGORIES.values()}
    moved_count = 0

    try:
        filenames = sorted(os.listdir(target_dir))
    except OSError as error:
        print(f"[!] Access error for directory '{target_dir}': {error}")
        return stats

    for filename in filenames:
        filepath = os.path.join(target_dir, filename)

        if not os.path.isfile(filepath):
            continue
        if not filename.lower().endswith(".txt"):
            continue
        if filename.lower() == "ingredients.txt":
            continue

        folder = get_category(filename)
        if folder is None:
            continue

        target_folder = os.path.join(target_dir, folder)
        target_path = os.path.join(target_folder, filename)

        if os.path.lexists(target_path):
            print(f"[-] Skipped (Destination already exists): {filename}")
            continue

        if dry_run:
            print(f"[*] [DRY RUN] Would move: {filename} -> {folder}/")
            stats[folder] += 1
            continue

        try:
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(filepath, target_path)
            stats[folder] += 1
            moved_count += 1
            print(f"[+] Moved: {filename} -> {folder}/")

        except PermissionError:
            print(f"[!] Permission denied: {filename}")
        except OSError as error:
            print(f"[!] Move error for '{filename}': {error}")

    if dry_run:
        print("\n[DRY RUN] Simulation completed. No files were moved.")
    else:
        print(f"\n[+] Successfully organized {moved_count} recipe file(s).")

    return stats
def load_recipe_data(recipe_path):
    try:
        with open(recipe_path, "r", encoding="utf-8") as file:
            lines = [line.strip() for line in file if line.strip()]

        if not lines:
            return None, None

        ingredients = {
            item.strip().lower()
            for item in lines[0].split(",")
            if item.strip()
        }

        instructions = lines[1:] if len(lines) > 1 else []

        return ingredients, instructions

    except Exception as error:
        print(
            f"[!] Error reading recipe '{os.path.basename(recipe_path)}': {error}"
        )
        return None, None

def suggest_recipes(target_dir, available_ingredients, category_choice):
    folder_path = os.path.join(target_dir, CATEGORIES[category_choice])

    try:
        filenames = sorted(os.listdir(folder_path))
    except FileNotFoundError:
        print("[-] No recipe folder found for this category yet.")
        return

    available_set = set(available_ingredients)
    suggestions = []

    for filename in filenames:
        recipe_path = os.path.join(folder_path, filename)

        if not os.path.isfile(recipe_path) or not filename.lower().endswith(
            ".txt"
        ):
            continue

        recipe_ingredients, instructions = load_recipe_data(recipe_path)

        if not recipe_ingredients:
            continue

        common_ingredients = recipe_ingredients.intersection(available_set)

        if common_ingredients:
            missing = sorted(recipe_ingredients - available_set)
            recipe_name = (
                os.path.splitext(filename)[0]
                .replace("_", " ")
                .replace("-", " ")
                .title()
            )
            suggestions.append((recipe_name, missing, instructions))

    if not suggestions:
        print("\n[-] No recipes match your current ingredients.")
        return

    print("\n" + "=" * 45)
    print(">>> RECIPE SUGGESTIONS & MISSING INGREDIENTS <<<")
    print("=" * 45)

    for name, missing, instructions in suggestions:
        print(f"\n- {name}")
        if missing:
            print(f"  * Missing Ingredients: {', '.join(missing)}")
        else:
            print("  * You have all ingredients in your inventory!")

        if instructions:
            print("  * Instructions:")
            for step in instructions:
                print(f"    {step}")
def read_ingredients(filename="ingredients.txt"):
    ingredients = []
    try:
        with open(filename, "r", encoding="utf-8") as file:
            for line in file:
                ingredient = line.strip().lower()
                if ingredient:
                    ingredients.append(ingredient)
    except FileNotFoundError:
        print(f"[!] '{filename}' not found. Starting with an empty inventory.")
    except Exception as error:
        print(f"[!] Could not read ingredient list: {error}")

    return ingredients


def main():
    parser = argparse.ArgumentParser(
        description="Smart Recipe Organizer & Kitchen Assistant"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview planned file moves without executing them.",
    )
    parser.add_argument(
        "--directory",
        default=".",
        help="Directory containing recipes and ingredients.txt.",
    )

    args = parser.parse_args()
    target_dir = os.path.abspath(args.directory)

    organize_files(target_dir=target_dir, dry_run=args.dry_run)

    if args.dry_run:
        print("\nExiting simulation mode.")
        return

    ingredients_path = os.path.join(target_dir, "ingredients.txt")
    available_ingredients = read_ingredients(ingredients_path)

    while True:
        try:
            shown_ingredients = ", ".join(available_ingredients) or "None"
            print(f"\n[Available Ingredients]: {shown_ingredients}")

            choice = (
                input(
                    "Select meal (breakfast / main / dessert) or 'q' to quit: "
                )
                .strip()
                .lower()
            )

            if choice == "q":
                print("Exiting Kitchen Assistant. Goodbye!")
                break

            if choice not in CATEGORIES:
                print(
                    "[-] Invalid choice. Please enter 'breakfast', 'main', 'dessert', or 'q'."
                )
                continue

            suggest_recipes(target_dir, available_ingredients, choice)

        except (KeyboardInterrupt, EOFError):
            print("\nProgram interrupted. Exiting safely.")
            break


if __name__ == "__main__":
    main()
                   