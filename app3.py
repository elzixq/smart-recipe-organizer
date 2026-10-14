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