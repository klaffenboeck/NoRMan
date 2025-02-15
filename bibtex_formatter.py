import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase

__all__ = ["BibtexFormatter"]

# NOTE: BibtexFormatter can currently only handle bibtex-string, does not directly interact with contents from CitationManager - must be changed!
class BibtexFormatter:
    def __init__(self, bibtex_string):
        self.original_bibtex = bibtex_string
        self.parser = bibtexparser.loads(bibtex_string)

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
