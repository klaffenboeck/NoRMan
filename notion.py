import requests
import json
import pprint
from authors import *
from config_handler import ConfigHandler

__all__ = ["NotionPage", "NotionAPI"]

class NotionAPI:
    def __init__(self, config_path='configs/notion_config.json'):
        self._load_config(config_path)
        self.headers = {
            "Authorization": f"Bearer {self.NOTION_TOKEN}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28",
        }
        self.mappings = self.load_mappings()

    def _load_config(self, config_path):
        with open(config_path, 'r') as file:
            notion_config = json.load(file)
        self.NOTION_TOKEN = notion_config["NOTION_TOKEN"]
        self.DATABASE_ID = notion_config["DATABASE_ID"]

    def request_pages(self, page_size=5):
        url = f"https://api.notion.com/v1/databases/{self.DATABASE_ID}/query"
        payload = {"page_size": page_size}
        response = requests.post(url, json=payload, headers=self.headers)
        data = response.json()

        with open('db.json', 'w', encoding='utf8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        return data.get("results", [])

    def load_mappings(self):
            """Load field mappings from bibtex_config.json using ConfigHandler."""
            config = ConfigHandler.load_config("bibtex_config.json")

            mappings = {}

            # Process bibtex_fields and special_fields
            for field_group in ["bibtex_fields", "special_fields"]:
                for entry in config.get(field_group, []):
                    if "notion" in entry and entry["notion"]:
                        field_name = entry["field"]
                        notion_key, notion_type = entry["notion"]
                        mappings[field_name] = (notion_key, notion_type)

            return mappings

    def request_page(self, title):
        url = f"https://api.notion.com/v1/databases/{self.DATABASE_ID}/query"
        payload = {
            "filter": {
                "property": "Key",
                "title": {"equals": title}
            }
        }
        # TODO: Make this call async
        response = requests.post(url, json=payload, headers=self.headers)
        page = NotionPage(response.json())
        return page

    def validate_key_availability(self, title):
        page = self.request_page(title)
        if page.json_data.get("results"):
            print("IS NOT AVAILABLE")
            return False
        print("IS AVAILABLE")
        return True

    def create_page(self, data):
        prepped_data = self.prep_data(data)
        #pprint.pprint(prepped_data)
        url = "https://api.notion.com/v1/pages"
        payload = {"parent": {"database_id": self.DATABASE_ID}, "properties": prepped_data}
        # TODO: make this call asynchronous
        res = requests.post(url, headers=self.headers, json=payload)
        print(res.status_code)
        if res.status_code != 200:
            j = res.json()
            pprint.pprint(j)
            raise ValueError(f"{j["code"]} ({j["status"]})\n{j["message"]}")
        return res

    def update_page(self, data):
        prepped_data = self.prep_data(data)
        url = f"https://api.notion.com/v1/pages/{data["notion_page_id"]}"
        payload = {"properties": prepped_data}
        res = requests.patch(url, headers=self.headers, json=payload)
        print(res.status_code)
        if res.status_code != 200:
            j = res.json()
            pprint.pprint(j)
            raise ValueError(f"{j["code"]} ({j["status"]})\n{j["message"]}")
        return res

# TODO: Move these mappings into config
    def prep_data(self, data):
        retdata = {}
        # mappings = {
        #     "key": ("Key", "title"),
        #     "papertrail": ("Papertrail", "rich_text"),
        #     "bibtex": ("Bibtex", "rich_text"),
        #     "year": ("Year", "number"),
        #     "title": ("Title", "rich_text"),
        #     "project": ("Project_tag", "multi_select"),
        #     "abstract": ("Abstract", "rich_text"),
        #     "count": ("Citation count", "number"),
        #     "type": ("Type", "select"),
        #     "notes": ("Notes", "rich_text"),
        #     "link_doi": ("Link/DOI", "url"),
        #     "journal": ("Journal", "rich_text"),
        #     "venue": ("Venue", "multi_select"),
        #     "authors": ("Authors", "multi_select"),
        #     "short_title": ("Short_title", "rich_text"),
        #     "short_title_manual": ("Short_title_manual", "checkbox")
        # }
        mappings = self.mappings

        for key, (notion_key, notion_type) in mappings.items():
            if key in data and data[key]:  # Ensure data[key] exists and is not empty
                if notion_type in ["title", "rich_text"]:
                    retdata[notion_key] = {notion_type: [{"text": {"content": data[key]}}]}
                elif notion_type == "number":
                    retdata[notion_key] = {notion_type: self.safe_int(data[key])}  # Default to 0 if invalid
                elif notion_type == "multi_select":
                    if isinstance(data[key], str):
                        retdata[notion_key] = {notion_type: [{"name": data[key]}]}  # Single string
                    elif isinstance(data[key], list):
                        retdata[notion_key] = {notion_type: [{"name": item} for item in data[key]]}  # List of names
                elif notion_type == "select":
                    retdata[notion_key] = {notion_type: {"name": data[key]}}
                elif notion_type in ["url","checkbox"]:
                    retdata[notion_key] = {notion_type: data[key]}
        return retdata

    def safe_int(self, value, default=""):
        """Convert a value to an integer safely, returning a default if conversion fails."""
        try:
            return int(value)  # Attempt to convert
        except (TypeError, ValueError):  # Handle None and invalid strings
            return default  # Return default value if conversion fails


class NotionPage:
    def __init__(self, json_data=None):
        """
        Initialize a NotionPage instance with JSON input.
        :param json_data: Dictionary containing Notion API structured data.
        """
        self.json_data = json_data if json_data else {}
        if self.json_data and self.json_data["object"] == "list":
            if len(self.json_data["results"]):
                self.notion_page_id = self.json_data["results"][0].get("id", {})
            else:
                self.json_data.get("id", {})

        # self.mappings = {
        #     "key": ("Key", "title"),
        #     "papertrail": ("Papertrail", "rich_text"),
        #     "bibtex": ("Bibtex", "rich_text"),
        #     "year": ("Year", "number"),
        #     "title": ("Title", "rich_text"),
        #     "project": ("Project_tag", "multi_select"),
        #     "abstract": ("Abstract", "rich_text"),
        #     "count": ("Citation count", "number"),
        #     "type": ("Type", "select"),
        #     "notes": ("Notes", "rich_text"),
        #     "link_doi": ("Link/DOI", "url"),
        #     "journal": ("Journal", "rich_text"),
        #     "venue": ("Venue", "select"),
        #     "authors": ("Authors", "multi_select"),
        #     "short_title": ("Short_title", "rich_text"),
        #     "short_title_manual": ("Short_title_manual", "checkbox")
        # }

        self.mappings = self.load_mappings()

        # Initialize attributes based on mappings
        for key, (notion_key, notion_type) in self.mappings.items():
            if key == "authors":
                # Apply AuthorList.from_array() for authors
                raw_authors = self.extract_value(notion_key, notion_type)
                setattr(self, key, AuthorList(raw_authors))
                setattr(self, f"_{key}", AuthorList(raw_authors))
            else:
                setattr(self, key, self.extract_value(notion_key, notion_type) if self.json_data else None)
                setattr(self, f"_{key}", self.extract_value(notion_key, notion_type) if self.json_data else None)
            # Dynamically create the _safe method for each key
            #setattr(self, f"_{key}", self.make_safe_method(key))


    def load_mappings(self):
            """Load field mappings from bibtex_config.json using ConfigHandler."""
            config = ConfigHandler.load_config("bibtex_config.json")

            mappings = {}

            # Process bibtex_fields and special_fields
            for field_group in ["bibtex_fields", "special_fields"]:
                for entry in config.get(field_group, []):
                    if "notion" in entry and entry["notion"]:
                        field_name = entry["field"]
                        notion_key, notion_type = entry["notion"]
                        mappings[field_name] = (notion_key, notion_type)

            return mappings


    def extract_value(self, notion_key, notion_type):
        """
        Extract a value from the JSON data based on its type.
        """
        if "results" not in self.json_data or not self.json_data["results"]:
            print("Error: 'results' key missing or empty in self.json_data")
            return None

        properties = self.json_data["results"][0].get("properties", {}) if self.json_data["object"] == "list" else self.json_data.get("properties", {})

        if notion_key not in properties:
            print(f"Error: notion_key '{notion_key}' not found in properties")
            return None

        notion_value = properties[notion_key]
        #print(f"Extracting {notion_type} from '{notion_key}'...")

        # Handling different notion types
        if notion_type in ["title", "rich_text"]:
            rich_text_data = notion_value.get(notion_type, [])
            if rich_text_data and isinstance(rich_text_data, list) and "text" in rich_text_data[0]:
                return rich_text_data[0]["text"].get("content", "")
            return ""

        elif notion_type == "number":
            return notion_value.get(notion_type, 0)  # Default to 0 if missing

        elif notion_type == "multi_select":
            return [item.get("name", "") for item in notion_value.get(notion_type, [])]

        elif notion_type == "select":
            select_data = notion_value.get(notion_type)
            return select_data["name"] if isinstance(select_data, dict) and "name" in select_data else ""

        elif notion_type == "url":
            return notion_value.get(notion_type, "")

        elif notion_type == "checkbox":
            return notion_value.get(notion_type, False)

        print(f"Warning: Unsupported notion_type '{notion_type}'")
        return None

    # def make_safe_method(self, key):
    #     """Returns a method that safely retrieves the attribute or an empty string."""
    #     def safe_method():
    #         value = getattr(self, key, None)  # Get the original value
    #         return value if value else ""  # Return empty string if None or empty
    #     return safe_method  # Return the function itself

    def get_value(self, key):
        """
        Get the value of a specific field.
        """
        if key in self.mappings:
            return getattr(self, key, None)
        raise KeyError(f"Key '{key}' not found in Notion mappings.")

    def set_value(self, key, value):
        """
        Set a new value for a specific field and update JSON data.
        """
        if key in self.mappings:
            notion_key, notion_type = self.mappings[key]
            if notion_type in ["title", "rich_text"]:
                self.json_data[notion_key] = {notion_type: [{"text": {"content": value}}]}
            elif notion_type == "number":
                self.json_data[notion_key] = {notion_type: int(value)}
            elif notion_type == "multi_select":
                self.json_data[notion_key] = {notion_type: [{"name": v} for v in value]}
            elif notion_type == "select":
                self.json_data[notion_key] = {notion_type: {"name": value}}
            elif notion_type in ["url","checkbox"]:
                self.json_data[notion_key] = {notion_type: value}
            setattr(self, key, value)
        else:
            raise KeyError(f"Key '{key}' not found in Notion mappings.")

    def get_json(self):
        """
        Get the modified Notion JSON data.
        """
        return self.json_data

    def get_bibtex(self):
        return self.json_data["results"][0]["properties"]["Bibtex"]["rich_text"][0]["text"]["content"]

    def safe_call(self, attribute):
        attr = getattr(self, attribute, None)


    def __repr__(self):
        return f"NotionPage({vars(self)})"
        """
        Returns a string representation of the object, listing all attributes
        defined in mappings without calling json_data.
        """
        # attr_values = {key: getattr(self, key, None) for key in self.mappings.keys()}
        # return f"NotionPage({attr_values})"
