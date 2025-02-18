import json
import os

__all__ = ["ConfigHandler"]

class ConfigHandler:
    """A utility class for loading JSON configuration files with caching support."""

    CONFIG_DIR = "configs"
    _instances = {}  # Class variable to cache instances per file

    def __new__(cls, file_name: str):
        """
        Ensures only one instance per configuration file exists.
        If an instance for the given file_name already exists, return it.
        """
        file_path = cls.get_full_path(file_name)

        if file_path not in cls._instances:
            instance = super().__new__(cls)
            instance.file_path = file_path
            instance.config = instance._load_config()
            cls._instances[file_path] = instance

        return cls._instances[file_path]

    @staticmethod
    def get_full_path(file_name: str) -> str:
        """
        Get the full path for the configuration file.
        If only a filename is provided, it will prepend the CONFIG_DIR path.
        """
        if os.path.isabs(file_name) or os.path.dirname(file_name):
            return file_name
        return os.path.join(ConfigHandler.CONFIG_DIR, file_name)

    def _load_config(self) -> dict:
        """
        Load and return JSON configuration data.
        """
        try:
            with open(self.file_path, 'r', encoding="utf-8") as file:
                data = json.load(file)
                print(f"Loaded JSON data from {self.file_path}")
                return data
        except FileNotFoundError:
            print(f"Error: {self.file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {self.file_path}.")
        return {}

    def get_config(self) -> dict:
        """Returns the loaded configuration."""
        return self.config

    def reload(self):
        """Reloads the configuration file and updates the cache."""
        self.config = self._load_config()

    @classmethod
    def load_config(cls, file_name: str) -> dict:
        """
        Class method that allows loading configuration without explicitly creating an instance.
        If the config is cached, it returns the cached version.
        """
        instance = cls(file_name)  # Calls __new__, ensuring caching
        return instance.get_config()
