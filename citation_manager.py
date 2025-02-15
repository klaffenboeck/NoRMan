import json
import re
import bibtexparser
from authors import Author, AuthorList
from config_handler import *
from bibtex_formatter import *
from output_formatter import *
from collections import Counter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

__all__ = ["CitationManager"]

class CitationManager:
    def __init__(self, config_path: str = "configs/config.json", style_config: str = "formatting_styles.json"):
        self.original_bibtex_file = ""
        self.modified_bibtex_file = ""
        self.original_bibtex_key = ""
        self.bibtex_url = ""
        self.bibtex_authors = ""
        self.bibtex_doi = ""
        self.year = ""
        #self.title = ""
        self.journal = ""
        self.abstract = ""
        self.venue = ""
        self.authors = None
        self.bibtex_data = None
        self.config_path = config_path
        self.style_config_path = style_config
        self.style_config_data = ConfigHandler.load_config(self.style_config_path)
        self.citation_key = ""
        self.papertrail = ""
        self.projects = []
        self.count = ""
        self.type = ""
        self.notes = ""
        self.bibtex_formatter = None
        self.output_formatter = HtmlCssFormatter()
        self._title = "" #self.title
        self._short_title_length = None  # Default short title length
        self._short_title = None  # Default short title    def __init__(self, title: str):
        self._short_title_set_manually = False

        self.stopwords = set(stopwords.words('english'))  # Load stopwords


    key = property(lambda self: self.citation_key)
    cite_count = property(lambda self: self.count)

    @property
    def title(self):
        return self._title

    # NOTE: title.setter not tested yet regarding _short_title_set_manually
    @title.setter
    def title(self, new_title: str):
        if self._title == new_title:
            return None
        self._title = new_title
        self.create_short_title()

    @property
    def short_title(self):
        return self._short_title

    @short_title.setter
    def short_title(self, new_short_title: str):
        self._short_title = new_short_title
        self._short_title_length = len(new_short_title.split())
        self._short_title_set_manually = True

    @property
    def short_title_length(self):
        return self._short_title_length

    @short_title_length.setter
    def short_title_length(self, length: int):
        self._short_title_length = length
        self.create_short_title(fixed_length=length)

    def reload_config(self):
        """Reloads the style configuration from the JSON file."""
        self.style_config_data = ConfigHandler.load_config(self.style_config_path)

    def parse_bibtex(self, bibtex):
        self.original_bibtex_file = bibtex
        self.bibtex_data = bibtexparser.loads(bibtex)

        for entry in self.bibtex_data.entries:
            if "ID" in entry:
                self.original_bibtex_key = entry["ID"]
            if "year" in entry:
                self.year = entry["year"]
            if "title" in entry:
                self.title = entry["title"]
            if "journal" in entry:
                self.journal = entry["journal"]
            elif "booktitle" in entry:
                self.journal = entry["booktitle"]
            if "abstract" in entry:
                self.abstract = entry["abstract"]
                del entry["abstract"]
            if "url" in entry:
                self.bibtex_url = entry["url"].strip()
            if "author" in entry:
                self.bibtex_authors = entry["author"]
                self.authors = AuthorList(entry["author"], self.config_path)
            if "doi" in entry:
                self.bibtex_doi = entry["doi"].strip()
            if "eprint" in entry:
                del entry["eprint"]

        self.bibtex_data.entries[0]["ID"] = self.get_citation_key()

        self.match_venue()
        self.set_link_doi()
        self.modified_bibtex_file = bibtexparser.dumps(self.bibtex_data)
        self.bibtex_formatter = BibtexFormatter(self.modified_bibtex_file)

    def set_link_doi(self):
        if self.bibtex_url:
            self.link_doi = self.bibtex_url
        elif self.bibtex_doi:
            match = re.search(r"(?:doi\\.org/|^/)(.+)", self.bibtex_doi)
            if match:
                self.link_doi = "https://doi.org/" + match.group(1)
            else:
                self.link_doi = "https://doi.org/" + self.bibtex_doi

    def match_venue(self):
        if not self.venue:
            return
        config_data = ConfigHandler.load_config(self.config_path)
        for mapping in config_data.get("venue_mapping", []):
            pattern = mapping.get("regex", "")
            if pattern and re.search(pattern, self.journal):
                self.venue = mapping.get("venue-mapping", "")
                return

    def generate_citation_key(self):
        fa = self.authors.first_author()
        self.citation_key = fa.get_citation_key(self.year)
        return self.citation_key

    def set_citation_key(self, key):
        self.citation_key = key

    def get_citation_key(self):
        return self.citation_key if self.citation_key else self.generate_citation_key()

    def create_short_title(self, fixed_length: int = None, **kwargs) -> str:
        if self._short_title_set_manually and self.short_title:
            return self.short_title
        self._short_title_length = fixed_length if fixed_length is not None else kwargs.get('max_words', 5)

        min_words = kwargs.get('min_words', 4)
        max_words = kwargs.get('max_words', 5)

        # Handle colons and dashes (prefer first part)
        title = re.split(r'[:\-]', self._title)[0].strip()

        # Tokenize and filter stopwords
        words = word_tokenize(title)
        content_words = [w for w in words if w.lower() not in self.stopwords and w.isalnum()]

        # Keep acronyms and capitalized words
        important_words = [w for w in content_words if w.istitle() or w.isupper()]
        if len(important_words) < min_words:
            important_words = content_words  # Fall back to all content words

        # Determine length based on title length
        title_length = len(title)
        if title_length <= 6:
            short_title = title  # Keep full title if 6 words or fewer
        else:
            dynamic_length = max(min_words, min(max_words, title_length // 2))
            short_title = important_words[:dynamic_length]

        if fixed_length is not None:
            short_title = important_words[:fixed_length]
        else:
            short_title = important_words[:dynamic_length]

        if short_title:
            short_title[0] = short_title[0].capitalize()

        self._short_title = ' '.join(short_title)
        self._short_title_length = len(short_title)
        self._short_title_set_manually = False
        return self._short_title


    def get(self, key, *args, **kwargs):
        print(f"Resolving {key} with args={args} and kwargs={kwargs}")
        if '.' in key:
            obj, method = key.split('.', 1)
            print(f"Object: {obj}, Method: {method}")

            obj_ref = getattr(self, obj, None)
            if obj_ref:
                print(f"Found object: {obj_ref}")
                if hasattr(obj_ref, method):
                    print(f"Calling method: {method} on {obj}")
                    return getattr(obj_ref, method)(*args, **kwargs)
                else:
                    print(f"Method {method} not found on {obj}")
            else:
                print(f"Object {obj} not found in CitationManager")

        formatter = kwargs.get("formatter", None)
        if formatter:
            value = getattr(self, key, '')
            # HACK: should actually take the object
            value = formatter.format_key(key, value)
            return value
        else:
            value = getattr(self, key, '')
            print(f"Returning direct attribute: {value}")
            return value

    def select_style_template(self, parameters: dict) -> str:
        style = parameters.get("style", "APA")
        encoding = parameters.get("encoding", "default")  # Reserved for future use
        bib_type = parameters.get("bib_type", "default")  # E.g., article, book, inproceedings

        style_data = self.style_config_data.get("journal_formatting_styles", {}).get(style, {})
        type_data = style_data.get(bib_type, style_data.get("default", {}))

        template = type_data.get("reference", "")
        return template

    def process_citation(self, parameters: dict):
        print("CALLED PROCESS_CITATION")
        template_str = self.select_style_template(parameters)

        def replace_conditionals(text):
            pattern = re.compile(r'\{\{(.*?)((?:##.*?##|\{\{.*?\}\})+)(.*?)\}\}', re.DOTALL)

            def conditional_replacer(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)

                markers = re.findall(r'##(.*?)##', content)

                if all(self.get(marker.strip(), formatter=self.output_formatter) for marker in markers):
                    content = replace_conditionals(content)
                    for marker in markers:
                        content = content.replace(f'##{marker}##', self.get(marker.strip(), formatter=self.output_formatter))
                    return f"{prefix}{content}{suffix}"
                return ''

            return pattern.sub(conditional_replacer, text)

        def replace_variables(text):
            pattern = re.compile(r'##(.*?)##')

            def variable_replacer(match):
                key = match.group(1).strip()
                return self.get(key, formatter=self.output_formatter)

            return pattern.sub(variable_replacer, text)

        def postprocess(text):
            # Check for final marker {{{.}}} and extract the desired final symbol
            final_marker_match = re.search(r'\{\{\{(.*?)\}\}\}$', text)
            final_symbol = final_marker_match.group(1) if final_marker_match else ''

            # Remove final marker from the text
            text = re.sub(r'\{\{\{.*?\}\}\}$', '', text)

            # Replace trailing non-alphanumeric characters, preserving ), ], >
            text = re.sub(r'([^\w\)\]\>]+)$', '', text)

            # Append the final symbol if it exists
            if final_symbol:
                if text.endswith((')', ']', '>')):
                    text = text[:-1] + final_symbol + text[-1]
                else:
                    text += final_symbol

            if self.output_formatter:
                return self.output_formatter.format_final_entry(text, id=self.get_citation_key())
            else:
                return text

        processed = replace_conditionals(template_str)
        processed = replace_variables(processed)
        processed = postprocess(processed)
        return processed
