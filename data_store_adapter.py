from abc import ABC, abstractmethod
from notion import *
from bibtex_handler import BibtexHandler

class DataStoreAdapter(ABC):
    """Abstract base class for data store adapters."""

    @abstractmethod
    def load(self, *args, **kwargs):
        """Loads data from the data store."""
        pass

    @abstractmethod
    def save(self, *args, **kwargs):
        """Saves data to the data store."""
        pass

    def validate_key(self, *args, **kwargs):
        """Validation method that must be overridden by subclasses."""
        raise NotImplementedError(f"{self.__class__.__name__} does not implement the 'validate' method.")

class NotionAdapter(DataStoreAdapter):
    """Adapter for interacting with Notion as a data store."""

    def __init__(self):
        """Initializes the Notion adapter with authentication details."""
        # self.notion_token = notion_token
        # self.database_id = database_id

    def load(self, reference):
        if not reference.key:
            raise ValueError("Reference key cannot be empty.")
        api = NotionAPI()
        page = api.request_page(reference.key)
        page.bibtex = BibtexHandler(reference, page.bibtex)
        reference.loaded_reference = page
        #breakpoint()
        return reference

    def save(self, reference):
        """Dummy save method for NotionAdapter."""
        #print("Saving data to Notion (dummy implementation).")
        api = NotionAPI()
        if reference.loaded_reference:
            api.update_page(reference.to_json())
        else:
            api.create_page(reference.to_json())

    def validate_key(self, reference):
        """Validates the key using the NotionAPI."""
        api = NotionAPI()
        try:
            if reference.__class__.__name__ == "Reference":
                api.validate_key_availability(reference.key)
            elif isinstance(reference, str):
                api.validate_key_availability(reference)
            else:
                raise ValueError(f"Invalid reference type: {type(reference).__name__}. Expected 'Reference' or 'str'.")
        except Exception as e:
            print(f"An error occurred during validation: {e}")
