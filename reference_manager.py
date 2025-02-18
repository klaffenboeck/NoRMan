import json
import os
from config_handler import ConfigHandler

class ReferenceManager:
    """Handles references by dynamically creating properties from a JSON config."""

    CONFIG_FILE = "configs/bibtex_config.json"  # Ensure the correct path

    def __init__(self):
        self._data = {}
        self.bibtex_fields = []  # Initialize early to prevent recursion issues
        self.bibtex_types = set()
        self._load_config()

    def _load_config(self):
        """Loads the BibTeX configuration and initializes properties."""
        config = ConfigHandler.load_config(self.CONFIG_FILE)

        self.bibtex_fields = [entry["field"] for entry in config.get("bibtex_fields", [])]
        self.bibtex_types = set(config.get("bibtex_types", []))

        for field in self.bibtex_fields:
            setattr(self, f"_{field}", None)

    def __setattr__(self, name, value):
        """Custom setter to trigger specific actions on title updates."""
        if name == "title":
            self.__dict__["_title"] = value
            self.create_short_title()
        elif hasattr(self, "bibtex_fields") and name in self.bibtex_fields:
            self.__dict__[f"_{name}"] = value
        else:
            super().__setattr__(name, value)

    def __getattr__(self, name):
        """Custom getter for dynamically assigned properties."""
        if "bibtex_fields" in self.__dict__ and name in self.bibtex_fields:
            return self.__dict__.get(f"_{name}", None)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @property
    def bibtex_type(self):
        return self.__dict__.get("_bibtex_type", None)

    @bibtex_type.setter
    def bibtex_type(self, value):
        """Ensures that bibtex_type is set only to allowed values."""
        if value not in self.bibtex_types:
            raise ValueError(f"Invalid bibtex_type: {value}. Must be one of {self.bibtex_types}.")
        self.__dict__["_bibtex_type"] = value

    def create_short_title(self):
        """Generates a short title when a title is assigned."""
        if self.title:
            words = self.title.split()
            self.short_title = " ".join(words[:3])  # Simple heuristic: first 3 words
        else:
            self.short_title = None
