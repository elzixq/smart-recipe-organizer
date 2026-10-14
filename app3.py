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