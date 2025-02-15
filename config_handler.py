import json
import os

__all__ = ["ConfigHandler"]

class ConfigHandler:
    """A utility class for loading JSON configuration files."""

    CONFIG_DIR = "configs"

    @staticmethod
    def get_full_path(file_name: str) -> str:
        """
        Get the full path for the configuration file. If only a filename is provided,
        it will prepend the CONFIG_DIR path.
        """
        if os.path.isabs(file_name) or os.path.dirname(file_name):
            return file_name
        return os.path.join(ConfigHandler.CONFIG_DIR, file_name)

    @staticmethod
    def load_config(file_name: str) -> dict:
        """
        Load and return JSON configuration data. Automatically looks in the 'configs/'
        directory if only a filename is provided.
        """
        file_path = ConfigHandler.get_full_path(file_name)
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                print(f"Loaded JSON data: {data}")
                return data
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {file_path}.")
        return {}
