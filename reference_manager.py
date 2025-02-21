import json
import os
from config_handler import ConfigHandler
from data_store_adapter import NotionAdapter
from bibtex_handler import BibtexHandler

class Reference:
    """Handles references by dynamically creating properties from a JSON config."""

    CONFIG_FILE = "configs/config.json"
    BIBTEX_CONFIG_FILE = "configs/bibtex_config.json"  # Ensure the correct path

    def __init__(self):
        self.loaded_reference = None
        self.__dict__["fields"] = []
        self._data = {}
        self.bibtex_types = set()

        self._load_config()

    def _load_config(self):
        """Loads the BibTeX configuration and initializes properties."""
        bibtex_config = ConfigHandler.load_config(self.BIBTEX_CONFIG_FILE)

        # Load fields from both "bibtex_fields" and "special_fields"
        self.fields = [
            entry["field"] for entry in bibtex_config.get("bibtex_fields", [])
        ] + [
            entry["field"] for entry in bibtex_config.get("special_fields", [])
        ]

        self.bibtex_types = set(bibtex_config.get("bibtex_types", []))

        for field in self.fields:
            setattr(self, f"_{field}", None)  # Initialize attributes dynamically

    # def __setattr__(self, name, value):
    #     """Custom setter to dynamically set fields and trigger specific actions."""
    #     if name == "title":
    #         self.__dict__["_title"] = value
    #         #self.create_short_title()
    #     elif hasattr(self, "fields") and name in self.fields:
    #         self.__dict__[f"_{name}"] = value
    #     else:
    #         super().__setattr__(name, value)

    def __setattr__(self, name, value):
        """Custom setter to dynamically set fields and defer to loaded_reference when applicable."""
        if name == "loaded_reference":
            super().__setattr__(name, value)
            return

        if self.loaded_reference and hasattr(self.loaded_reference, name):
            setattr(self.loaded_reference, name, value)
        elif name in self.fields:
            self.__dict__[f"_{name}"] = value
        else:
            super().__setattr__(name, value)



    # def __getattr__(self, name):
    #     """Custom getter for dynamically assigned properties with Notion-based fallback values."""
    #     if "fields" in self.__dict__ and name in self.fields:
    #         value = self.__dict__.get(f"_{name}", None)

    #         # Load configuration and retrieve notion mappings from both bibtex_fields and special_fields
    #         bibtex_config = ConfigHandler.load_config(self.BIBTEX_CONFIG_FILE)
    #         notion_mappings = {
    #             entry["field"]: entry.get("notion", [])  # Ensure 'notion' is accessed safely
    #             for field_category in ["bibtex_fields", "special_fields"]
    #             for entry in bibtex_config.get(field_category, [])
    #         }

    #         # Determine the appropriate fallback value based on the Notion field type
    #         if name in notion_mappings and notion_mappings[name]:
    #             notion_tag = notion_mappings[name]
    #             notion_type = notion_tag[1] if len(notion_tag) > 1 else None  # Ensure at least one entry exists
    #             if notion_type == "multi_select":
    #                 return value if value is not None else []
    #             elif notion_type == "rich_text":
    #                 return value if value is not None else ""
    #             # Extend handling for other Notion data types if needed

    #         return value if value is not None else None  # Explicitly return None for consistency

    #     raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __getattr__(self, name):
        """Custom getter to check loaded_reference before accessing local attributes."""
        # Avoid recursion by checking __dict__ directly
        if name == "loaded_reference":
            return self.__dict__.get("loaded_reference", None)

        if "fields" not in self.__dict__:
            # If fields is not yet initialized, avoid recursion
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        if self.loaded_reference and hasattr(self.loaded_reference, name):
            return getattr(self.loaded_reference, name)

        if name in self.__dict__["fields"]:  # Access fields directly from __dict__
            value = self.__dict__.get(f"_{name}", None)

            # Load Notion mappings only if we have a loaded_reference (to avoid unnecessary loading)
            bibtex_config = ConfigHandler.load_config(self.BIBTEX_CONFIG_FILE)
            notion_mappings = {
                entry["field"]: entry.get("notion", [])
                for field_category in ["bibtex_fields", "special_fields"]
                for entry in bibtex_config.get(field_category, [])
            }

            if name in notion_mappings and notion_mappings[name]:
                notion_type = notion_mappings[name][1] if len(notion_mappings[name]) > 1 else None
                if notion_type == "multi_select":
                    return value if value is not None else []
                elif notion_type == "rich_text":
                    return value if value is not None else ""

            return value

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
            """Placeholder for title shortening logic."""
            if self._title:
                self._short_title = self._title[:10] + "..." if len(self._title) > 10 else self._title

    def __repr__(self):
        return f"Reference({vars(self)})"

class ReferenceManager:
    """Manages references and proxies attribute settings to a contained Reference instance."""

    def __init__(self):
        self.reference = Reference()  # Holds a single reference instance

    def __setattr__(self, name, value):
        """Proxy attribute setting to the reference instance."""
        if name == "reference":
            super().__setattr__(name, value)
        elif name == "bibtex":
            setattr(self.reference, name, BibtexHandler(self.reference, value))
        elif name == "title":
            setattr(self.reference, name, value)
            if not self.reference.short_title:
                self.short_title = self.create_short_title()
                self.short_title_manual = False
            elif not self.reference.short_title_manual:
                self.short_title = self.create_short_title()
                self.short_title_manual = False
        elif name == "short_title":
            setattr(self.reference, name, value)
            setattr(self.reference, "short_title_manual", True)
        else:
            setattr(self.reference, name, value)

    def create_short_title(self, max_length=30):
        """Creates a short title truncated after max_length characters with ellipses if needed."""
        return self.title if len(self.title) <= max_length else self.title[:max_length].rstrip() + "..."



    def __getattr__(self, name):
        """Proxy attribute getting to the reference instance."""
        return getattr(self.reference, name)

    def load_reference(self):
        """Loads a reference using NotionAdapter and stores it."""
        if not self.reference or not self.reference.key:
            raise ValueError("Reference key cannot be empty.")

        adapter = NotionAdapter()
        try:
            new_reference = adapter.load(self.reference)
            self.reference = new_reference  # Only update if successful
        except ValueError as e:
            print(f"Error loading reference: {e}")
