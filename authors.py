import re
import json
from abc import ABC, abstractmethod
from types import MethodType
from typing import TYPE_CHECKING
import pprint
from unidecode import unidecode

if TYPE_CHECKING:
    from output_formatter import OutputFormatter  # Only for type hints, no runtime import


__all__ = ["Author", "AuthorList"]

class Author:
    def __init__(self, bibtex_string: str, config_path: str = "configs/config.json"):
        """Initialize an Author object from a BibTeX-formatted name string."""
        self.original_bibtex = bibtex_string.strip()
        self.fullname = ""
        # Parse the BibTeX name
        self.firstname = ""
        self.lastname = ""
        self.von_part = ""
        self.suffix = ""
        self.sorting_key = ""
        self.citation_key = ""

        # Load special surnames from config
        self.special_surnames = self._load_special_surnames(config_path)

        self._parse_bibtex_name()

    def initials(self, name_str, delim=''):
        # Step 1: Split along whitespace and special characters
        # Adding more common name-related special characters: ., :, _, (, ), [, ], {, }, &, @, !
        parts = re.split(r"[ \-'/.:_()\[\]{}&@!]", name_str)

        # Step 2: Further split each part along capital letters without removing them

        initials = ""
        for part in parts:
            if part:  # Avoid processing empty strings
                split_parts = []
                split_parts.extend(re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', part))
                if len(split_parts) > 1:
                    if(split_parts[0].istitle()):

                        initials += split_parts.pop(0)
                initials += "".join([p[0] for p in split_parts if p])
                initials += delim

        return initials.strip()


    def _load_special_surnames(self, config_path):
        """Load special surnames from config.json."""
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = json.load(f)
            return set(config_data.get("special_surnames", []))
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading config: {e}")
            return set()

    def css_class(self):
        name = ''.join([self.firstname, self.von_part, self.lastname, self.suffix]).strip()
        decoded = unidecode(name)
        return re.sub(r'[^a-zA-Z0-9_]', '', decoded).lower()


    def _parse_bibtex_name(self):
        """Parses a BibTeX-style name and assigns attributes correctly."""
        parts = self.original_bibtex.split(",")

        if len(parts) == 3:  # Expected format: Last, First, Suffix
            last, first, self.suffix = map(str.strip, parts)
            self.fullname = first.strip() + " " + last.strip() + ", " + self.suffix
        elif len(parts) == 2:  # Common format: Last, First
            last, first = map(str.strip, parts)
            self.fullname = " ".join([first, last]).strip()
            self._split_von_part_lastname(last)
            self._split_firstname_von_part(first)
        else:  # No comma: Assume standard first-last order
            self.fullname = self.original_bibtex
            name_parts = self.original_bibtex.split()
            self.lastname = name_parts.pop()  # Last word = last name
            first = " ".join(name_parts)  # Everything else = first name
            self._split_firstname_von_part(first)

        # Extract surname prefix if applicable
        self.sorting_key = self._generate_sorting_key()

    def _split_von_part_lastname(self, last):
        """Extracts von parts (surname prefixes) from the last name."""
        lastname, von_part = [],[]
        last_parts = last.split()
        lastname.append(last_parts.pop())
        while last_parts and last_parts[0].islower():
            von_part.append(last_parts.pop(0))

        last_parts_str = " ".join(last_parts).strip()
        lastname_str = " ".join(lastname).strip()
        self_lastname = last_parts_str + " " + lastname_str
        self.lastname = self_lastname.strip()
        von_part_str = " ".join(von_part)
        self.von_part = " ".join([self.von_part, von_part_str]).strip()


    def _split_firstname_von_part(self, first):
        firstname = []
        first_parts = first.split()
        firstname.append(first_parts.pop(0))
        self.veryfirstnameonly = firstname[0]
        while first_parts and first_parts[0][0].isupper():
            firstname.append(first_parts.pop(0))

        self.firstname = " ".join(firstname)
        von_part_str = " ".join(first_parts)
        self.von_part = " ".join([von_part_str, self.von_part]).strip()

    def _generate_sorting_key(self):
        """Generates a sorting key for correct ordering of authors."""
        if self.lastname and "-" in self.lastname and self.lastname[0].islower():
            return self.lastname.split("-", 1)[1]  # Use only part after hyphen
        return self.lastname  # Default to lastname

    def lastname_display(self):
        """Returns the full last name including the von_part."""
        return f"{self.von_part} {self.lastname}".strip()

    def initialize_firstname(self, dot="."):
        words = self.firstname.split()
        allinitials = []
        for part in words:
            subparts = part.split("-")
            initials = []
            for subpart in subparts:
                initial = subpart[0] + dot
                initial = initial.strip()
                initials.append(initial)
            partinitials = "-".join(initials) if dot else "".join(initials)
            partinitials = partinitials.strip()
            allinitials.append(partinitials)
        final = " ".join(allinitials) if dot else "".join(allinitials)
        return final.strip()


    def initialize_firstname_2(self, dot="."):
        all_initials = [
            "-".join(subpart[0] + dot for subpart in part.split("-")).strip()
            if dot else "".join(subpart[0] for subpart in part.split("-")).strip()
            for part in self.firstname.split()
        ]
        return " ".join(all_initials).strip() if dot else "".join(all_initials).strip()


    def middlename(self):
        """Returns the middle name(s), which is everything in firstname except the first word."""
        parts = self.firstname.split()
        return " ".join(parts[1:]) if len(parts) > 1 else ""

    def veryfirstnameonly(self):
        """Returns only the very first name."""
        return self.firstname.split()[0] if self.firstname else ""

    def format_plain(self):
        return self.fullname.strip()

    def format_alpha(self):
        """Returns the author name formatted for the alpha BibTeX style."""
        parts = [self.von_part, self.lastname + ",", self.firstname, self.suffix]
        return " ".join(filter(None, parts))

    def format_apalike(self):
        """Returns the author name formatted for the apalike BibTeX style (Last, F.)."""
        parts = [self.von_part, self.lastname + ",", self.initialize_firstname(), self.suffix]
        return " ".join(filter(None, parts))

    def format_ieeetr(self):
        """Returns the author name formatted for the ieeetr BibTeX style (F. Last)."""
        parts = [self.initialize_firstname(), self.von_part, self.lastname, self.suffix]
        return " ".join(filter(None, parts))

    def __repr__(self):
        """Provides a string representation for debugging."""
        return (f"Author(firstname='{self.firstname}', lastname='{self.lastname}', "
                f"von_part='{self.von_part}', suffix='{self.suffix}', sorting_key='{self.sorting_key}')")

    def generate_citation_key(self, addon=""):
        """Generate the citation key based on last name, special surnames, and formatted addon."""
        # Ensure addon is a string
        if isinstance(addon, int):
            addon = str(addon)  # Convert number to string

        match = re.search(r"\d{4}", addon)  # Find the first occurrence of four digits
        if match:
            addon = addon[match.start():]  # Keep only the part starting from the four digits

        if self.lastname in self.special_surnames:
            self.citation_key = f"{self.lastname}{self.firstname}{addon}"
        else:
            self.citation_key = f"{self.lastname}{addon}"

    def get_citation_key(self, addon=""):
        if addon:
            self.generate_citation_key(addon)
        elif not self.citation_key:
            self.generate_citation_key()
        return self.citation_key

    def format(self, *args, **kwargs):
        pprint.pprint(kwargs)
        formatter = kwargs.pop('formatter', None)

        if formatter:
            return formatter.format_author(self, *args, **kwargs)
        else:
            return self._format(*args, **kwargs)


    def _format(self, *args):
        print("_format is called")
        """Private method to format the author name using attributes and strings."""
        result = []
        for arg in args:
            if hasattr(self, arg):
                value = getattr(self, arg)
                if value:
                    result.append(value)
            else:
                result.append(arg)
        formatted_string = ''.join(result)
        cleaned_string = re.sub(r'\s+', ' ', formatted_string).strip()
        return cleaned_string


for attr in ['fullname', 'firstname', 'lastname', 'von_part', 'suffix']:
    def prop(self, attr=attr):
        return self.initials(getattr(self, attr))
    setattr(Author, f"{attr}_initials", property(prop))

for attr in ['fullname', 'firstname', 'lastname', 'von_part', 'suffix']:
    def prop(self, attr=attr):
        return self.initials(getattr(self, attr), ". ")
    setattr(Author, f"{attr}_abbr", property(prop))



class AuthorList:
    def __init__(self, authors=None, config_path="configs/config.json"):
        """
        Initialize an AuthorList with a single string, a list of strings, or None.

        :param authors: A string of author names separated by " and ", a list of author names, or None.
        :param config_path: Path to the configuration file.
        """
        if authors is None:
            self.original = ""
            self.authors = []
        elif isinstance(authors, str):
            self.original = authors.strip()
            self.authors = [Author(name.strip(), config_path) for name in self.original.split(" and ")]
        elif isinstance(authors, list):
            self.original = " and ".join(authors)
            self.authors = [Author(name.strip(), config_path) for name in authors]
        else:
            raise TypeError("authors must be a string, a list of strings, or None")

        self._load_formatting_styles("configs/formatting_styles.json")

    def _load_formatting_styles(self, path):
        """Load formatting styles from a JSON file and dynamically attach methods for formatting."""
        with open(path, 'r') as file:
            styles = json.load(file).get("authorlist_formatting_styles", {})

        for style_name, (args, kwargs) in styles.items():
            method_name = f"format_{style_name}_style"

            def inside_formatter(self, *fmt_args, args=args, kwargs=kwargs, formatter=None, **fmt_kwargs):
                combined_kwargs = {**kwargs, **fmt_kwargs}
                if formatter:
                    combined_kwargs['formatter'] = formatter
                return self.format(*args, **combined_kwargs)

            setattr(self, method_name, MethodType(inside_formatter, self))

    @classmethod
    def from_array(cls, array, config="configs/config.json"):
        return cls(" and ".join(array), config)

    def __repr__(self):
        return f"AuthorList(authors={self.authors})"

    def __iter__(self):
        return iter(self.authors)

    def __len__(self):
        return len(self.authors)

    def __getitem__(self, index):
        return self.authors[index]

    def __str__(self):
        return self.get_string()

    def first_author(self):
        """Returns the first author in the list, or None if empty."""
        return self.authors[0] if self.authors else None

    def last_author(self):
        """Returns the last author if there are at least two authors; otherwise, None."""
        return self.authors[-1] if len(self.authors) > 1 else None

    def sorted_by_lastname(self):
        """Returns a new list of authors sorted by last name (ignoring surname_prefix)."""
        return sorted(self.authors, key=lambda author: author.sorting_key.lower())

    def get_array(self):
        authors = []
        for author in self.authors:
            authors.append(author.fullname)
        return authors

    def get_string(self, delim=", "):
        try:
            arr = self.get_array()
            return delim.join(arr)
        except Exception as e:  # Catch any exception and handle it
            print(f"Error in get_string: {e}")  # Optional: Log the error
            return ""  # Return an empty string as a fallback

    def format(self, *args, **kwargs):
        formatter = kwargs.get('formatter', None)

        if formatter:
            return formatter.format_authors(self, *args, **kwargs)
        else:
            return self._format(*args, **kwargs)

    def _format(self, *args, **kwargs):
        delim = kwargs.get('delim', ', ')
        conjunction = kwargs.get('conjunction', ' and ')
        delim_suffix = kwargs.get('delim_suffix', '')
        first_author_format = kwargs.get('first_author_format', None)
        cutoff = kwargs.get('cutoff', None)
        cutoff_phrase = kwargs.get('cutoff_phrase', ' et al.')
        formatter = kwargs.get('formatter', None)
        #pprint.pprint(formatter)

        if isinstance(conjunction, (list, tuple)) and len(conjunction) == 2:
            conjunction_two, conjunction_three_or_more = conjunction
        else:
            conjunction_two = conjunction_three_or_more = conjunction

        def format_author(author, *format_args, **format_kwargs):
            return author.format(*format_args, **format_kwargs)

        formatted_authors = []
        if first_author_format:
            formatted_authors.append(format_author(self.authors[0], *first_author_format, formatter=formatter))
            formatted_authors.extend(format_author(author, *args, formatter=formatter) for author in self.authors[1:])
        else:
            formatted_authors = [format_author(author, *args, formatter=formatter) for author in self.authors]

        if cutoff and len(formatted_authors) >= cutoff:
            return f"{formatted_authors[0]}{cutoff_phrase}"

        if not formatted_authors:
            return ""
        elif len(formatted_authors) == 1:
            return formatted_authors[0]
        elif len(formatted_authors) == 2:
            return conjunction_two.join(formatted_authors)
        else:
            return delim.join(formatted_authors[:-1]) + conjunction_three_or_more + formatted_authors[-1]
