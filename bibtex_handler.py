import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bparser import BibTexParser
from config_handler import ConfigHandler
from authors import AuthorList

__all__ = ["BibtexHandler"]

class BibtexHandler:
    def __init__(self, reference, bibtex_string=""):
        self.original_bibtex = bibtex_string
        self.original_order = []
        self.modified_bibtex = ""
        self.reference = reference
        #self.parser = bibtexparser.loads(bibtex_string)
        self.parser = bibtexparser.loads(bibtex_string, parser=self.custom_parser())
        self.bibtex_config = ConfigHandler.load_config("configs/bibtex_config.json")

        if bibtex_string:
            self.parse_bibtex(bibtex_string)
            # self.get_field_order()

    @property
    def formatted(self):
        """Returns the formatted BibTeX entry as a string."""
        return self.get_formatted()

    def parse_bibtex(self, bibtex_string):
        """Parses the BibTeX string and stores its values into reference."""
        if not self.valid_bibtex(bibtex_string):
            return
        parsed_bibtex = bibtexparser.loads(bibtex_string)

        # Assuming we only process the first entry in the BibTeX
        if parsed_bibtex.entries:
            entry = parsed_bibtex.entries[0]

            self.reference.original_key = entry.pop("ID", None)
            self.reference.original_entrytype = entry.pop("ENTRYTYPE", None)
            self.reference.entrytype = self.reference.original_entrytype
            #breakpoint()
            for key in list(entry.keys()):  # Copy keys before iterating
                value = entry[key]
                setattr(self.reference, key, value)

                if key in ["abstract", "eprint"]:
                    del entry[key]  # Now safe because we're iterating over a copy

                if key == "author":
                    self.reference.authors = AuthorList(entry.get("author", None))

            if self.reference.key:
                entry["ID"] = self.reference.key
            elif self.reference.authors.first_author():
                year = self.reference.year
                self.reference.key = self.reference.authors.first_author().get_citation_key(year)
                entry["ID"] = self.reference.key
            else:
                entry["ID"] = self.reference.original_key
            entry["ENTRYTYPE"] = self.reference.entrytype
            self.modified_bibtex = bibtexparser.dumps(parsed_bibtex)

    # def get_field_order(self):
    #     entry = self.parser.entries[0]
    #     breakpoint()
    #     self.original_order = [field[0] for field in entry["fields"]]

    def get_formatted(self):
        db = BibDatabase()
        entry = {}
        fields = [field_dict["field"] for field_dict in self.bibtex_config["bibtex_fields"]]

        entry["ID"] = self.reference.key
        entry["ENTRYTYPE"] = self.reference.entrytype
        for field in fields:
            if field == "abstract":
                continue
            if field == "author" and getattr(self.reference, field):
                entry["author"] = self.reference._authors.get_string(" and ")
            elif getattr(self.reference, field):
                entry[field] = str(getattr(self.reference, field)).strip()
        #entry["title"] = self.reference.title
        #breakpoint()
        db.entries = [entry]
        writer = BibTexWriter()
        return writer.write(db)


    def original(self):
        return self.original_bibtex

    def reformat(self, order=["author", "title", "year", "journal"]):
        # Step 1: Remove empty lines and reduce multiple spaces to one
        lines = self.original_bibtex.splitlines()
        cleaned_lines = [" ".join(line.split()) for line in lines if line.strip()]
        cleaned_bibtex = "\n".join(cleaned_lines)

        # Step 2: Reorder fields based on provided order
        db = bibtexparser.loads(cleaned_bibtex)
        writer = BibTexWriter()
        writer.indent = '    '
        reordered_entries = []

        for entry in db.entries:
            reordered_entry = {}

            # Add fields based on the provided order
            for key in order:
                if key in entry:
                    reordered_entry[key] = entry.pop(key)

            # Add the remaining fields in their original order
            reordered_entry.update(entry)
            reordered_entries.append(reordered_entry)

        # Create a new database and write the reordered entries
        new_db = BibDatabase()
        new_db.entries = reordered_entries

        return writer.write(new_db)

    reformatted = reformat

    def reduce(self, fields=["author", "title", "journal", "year"]):
        db = self.parser
        reduced_entries = []

        for entry in db.entries:
            # Always keep 'ENTRYTYPE' and 'ID', and include fields that are non-empty
            reduced_entry = {
                k: v for k, v in entry.items()
                if k in fields and v.strip()
            }

            # Ensure ENTRYTYPE and ID are preserved
            reduced_entry["ENTRYTYPE"] = entry.get("ENTRYTYPE", "article")  # Default to 'article' if missing
            reduced_entry["ID"] = entry.get("ID", "missing_id")  # Provide a default ID if missing

            reduced_entries.append(reduced_entry)

        # Create a new database and write the reduced entries
        new_db = BibDatabase()
        new_db.entries = reduced_entries

        writer = BibTexWriter()
        writer.indent = '    '

        return writer.write(new_db)

    reduced = reduce

    def valid_bibtex(self, bibtex):
        print("CALLED valid_bibtex ")
        if isinstance(bibtex, str):
            try:
                bibtex = bibtexparser.loads(bibtex)
            except Exception:
                return False  # Invalid BibTeX string

        # Ensure bibtex is a valid parsed object with entries
        return bool(getattr(bibtex, "entries", []))

    def __str__(self):
        return f"{self.formatted}"

    def __repr__(self):
        return f"bibtexHandler({vars(self)})"

    def custom_parser(self):
        print("custom_parser involved")
        parser = BibTexParser()
        parser.ignore_nonstandard_types = False
        parser.common_strings = True
        parser.interpolate_strings = True
        parser.preserve_field_order = True  # This keeps the field order
        return parser
