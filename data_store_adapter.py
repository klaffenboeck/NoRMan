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
        return reference

    def save(self, *args, **kwargs):
        """Dummy save method for NotionAdapter."""
        print("Saving data to Notion (dummy implementation).")
