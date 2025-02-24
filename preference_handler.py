import json
import os

class PreferenceHandler:
    _cache = None
    _cache_path = "configs/preferences.json"

    @classmethod
    def _load_preferences(cls):
        """Load preferences from the JSON file, handling empty or invalid files."""
        if cls._cache is None:
            if os.path.exists(cls._cache_path):
                try:
                    with open(cls._cache_path, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        cls._cache = json.loads(content) if content else {}
                except (json.JSONDecodeError, OSError):
                    cls._cache = {}  # Fallback to empty dictionary if invalid
            else:
                cls._cache = {}
        return cls._cache

    @classmethod
    def get(cls, key, default=None):
        """Retrieve a preference value."""
        prefs = cls._load_preferences()
        return prefs.get(key, default)

    @classmethod
    def set(cls, key, value):
        """Set a preference value and save immediately."""
        prefs = cls._load_preferences()
        if prefs.get(key) != value:
            prefs[key] = value
            cls._save_preferences()

    @classmethod
    def _save_preferences(cls):
        """Save the cached preferences to the JSON file."""
        with open(cls._cache_path, "w", encoding="utf-8") as f:
            json.dump(cls._cache, f, indent=4)

    @classmethod
    def reset(cls):
        """Reset the cached preferences, forcing a reload from the file."""
        cls._cache = None
