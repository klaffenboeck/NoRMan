import json
import os
import tkinter as tk
from tkinter import ttk

class KeyHandler:
    def __init__(self, filename="configs/key_store.json"):
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        self.filename = filename
        self.keys = self._load_keys()

    def _load_keys(self):
        """Loads keys from JSON file, ensuring they are sorted."""
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r", encoding="utf-8") as file:
                    keys = json.load(file)
                    return sorted(set(keys))  # Ensure uniqueness and sorting
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _save_keys(self):
        """Saves the sorted keys back to the JSON file."""
        with open(self.filename, "w", encoding="utf-8") as file:
            json.dump(self.keys, file, indent=2)

    def add_key(self, key):
        """Adds a key, ensuring uniqueness and sorting."""
        if key and key not in self.keys:
            self.keys.append(key)
            self.keys.sort()
            self._save_keys()

    def remove_key(self, key):
        """Removes a key if it exists and updates the JSON file."""
        if key in self.keys:
            print(f"Removing key: {key}")  # Debugging
            self.keys.remove(key)
            self._save_keys()  # Ensure the file updates


    def get_keys(self):
        """Returns the sorted list of keys."""
        return self.keys

class AutocompleteCombobox(ttk.Combobox):
    def __init__(self, master, key_handler, **kwargs):
        super().__init__(master, **kwargs)
        self.key_handler = key_handler
        self['values'] = self.key_handler.get_keys()
        #self.bind('<KeyRelease>', self._on_keyrelease)

    def _on_keyrelease(self, event):
        value = self.get()

        # Reset dropdown values
        full_list = self.key_handler.get_keys()
        self['values'] = full_list

        # If input is empty, reset values but don't filter
        if value == '':
            return

        # Filter matching values
        matching_values = [item for item in full_list if item.lower().startswith(value.lower())]

        # Update the dropdown list without forcing selection
        self['values'] = matching_values if matching_values else full_list



    def add_key(self):
        key = self.get().strip()
        if key:
            self.key_handler.add_key(key)
            self['values'] = self.key_handler.get_keys()
