# import os
# import shutil
# import subprocess
# import sys

# class PdfHandler:
#     def __init__(self, papers_path):
#         """Initialize the handler with the base path for storing PDFs."""
#         self.papers_path = os.path.expanduser(papers_path)
#         self.pdf_path = None

#     def select_pdf_file(self, file_path):
#         """Set the selected PDF file path if valid."""
#         if file_path and os.path.isfile(file_path):
#             self.pdf_path = file_path
#             return self.pdf_path
#         raise FileNotFoundError("Invalid file selected.")

#     def rename_and_move_pdf(self, key_content):
#         """Rename and move the selected PDF file."""
#         if not self.pdf_path:
#             raise ValueError("No PDF file selected.")
#         if not os.path.isfile(self.pdf_path):
#             raise FileNotFoundError("Selected PDF file does not exist.")
#         if not key_content.strip():
#             raise ValueError("Key content is empty.")

#         destination_file = os.path.join(self.papers_path, f"{key_content}.pdf")

#         if os.path.exists(destination_file):
#             raise FileExistsError(f"A file with the name {key_content}.pdf already exists.")

#         os.makedirs(self.papers_path, exist_ok=True)
#         shutil.move(self.pdf_path, destination_file)
#         self.pdf_path = destination_file
#         return self.pdf_path

#     def find_paper_path(self, key_content, **kwargs):
#         """Check if a PDF with the given key_content exists in papers_path."""
#         paper_path = os.path.join(self.papers_path, f"{key_content}.pdf")
#         if os.path.exists(paper_path):
#             self.pdf_path = paper_path
#             return paper_path
#         return ""

#     def open_pdf(self):
#         """Open the stored PDF file with the default viewer."""
#         if not self.pdf_path or not os.path.isfile(self.pdf_path):
#             raise FileNotFoundError("No valid PDF file to open.")

#         if os.name == "nt":  # Windows
#             os.startfile(self.pdf_path)
#         elif os.name == "posix":  # macOS or Linux
#             subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", self.pdf_path])
#         else:
#             raise OSError("Unsupported operating system.")


import os
import shutil
import subprocess
import sys


class PdfHandler:
    def __init__(self, papers_path):
        """Initialize the handler with the base path for storing PDFs."""
        self.papers_path = os.path.expanduser(papers_path)
        self.pdf_path = None  # Initially a string, becomes a dict after rename_and_move_pdf

    def select_pdf_file(self, file_path):
        """Set the selected PDF file path if valid."""
        if file_path and os.path.isfile(file_path):
            self.pdf_path = file_path
            return self.pdf_path
        raise FileNotFoundError("Invalid file selected.")

    def rename_and_move_pdf(self, key_content):
        """Rename and move the selected PDF file. Converts pdf_path to a dictionary."""
        if not self.pdf_path:
            raise ValueError("No PDF file selected.")
        if not os.path.isfile(self.pdf_path):
            raise FileNotFoundError("Selected PDF file does not exist.")
        if not key_content.strip():
            raise ValueError("Key content is empty.")

        destination_file = os.path.join(self.papers_path, f"{key_content}.pdf")

        if os.path.exists(destination_file):
            raise FileExistsError(f"A file with the name {key_content}.pdf already exists.")

        os.makedirs(self.papers_path, exist_ok=True)
        shutil.move(self.pdf_path, destination_file)

        # Convert pdf_path to a dictionary with 'main' as the default entry
        self.pdf_path = {"main": destination_file}
        return self.pdf_path

    def duplicate(self, folder, **kwargs):
        """Duplicate the main PDF file into the specified folder inside papers_path."""
        # If main does not exist but pdf_path is a string, rename_and_move_pdf first
        if not isinstance(self.pdf_path, dict):
            if isinstance(self.pdf_path, str) and os.path.isfile(self.pdf_path):
                base_name = os.path.basename(self.pdf_path)
                key_content, _ = os.path.splitext(base_name)
                self.rename_and_move_pdf(key_content)
            else:
                raise ValueError("No valid PDF file available for duplication.")

        main_pdf = self.pdf_path.get("main")
        if not main_pdf or not os.path.isfile(main_pdf):
            raise FileNotFoundError("Main PDF file does not exist.")

        destination_folder = os.path.join(self.papers_path, folder)
        os.makedirs(destination_folder, exist_ok=True)

        filename = os.path.basename(main_pdf)
        base_name, ext = os.path.splitext(filename)

        # Handle prepend and append kwargs
        prepend = kwargs.get("prepend", "")
        append = kwargs.get("append", "")

        new_filename = f"{prepend}{base_name}{append}{ext}"
        new_pdf_path = os.path.join(destination_folder, new_filename)

        shutil.copy2(main_pdf, new_pdf_path)
        self.pdf_path[folder] = new_pdf_path
        return new_pdf_path

    def find_paper_path(self, key_content, version="main"):
        """Find a PDF file based on key_content inside the specified version folder.

        - If version="main", it looks in the main papers directory **for an exact match**.
        - If version is a folder name, it looks inside that folder for a file that **contains** key_content.
        """
        search_path = (
            self.papers_path if version == "main"
            else os.path.join(self.papers_path, version)
        )

        if not os.path.isdir(search_path):
            self.pdf_path = None  # Reset pdf_path if folder does not exist
            return ""

        # Exact match for the main directory
        if version == "main":
            exact_paper_path = os.path.join(search_path, f"{key_content}.pdf")
            if os.path.exists(exact_paper_path):
                self.pdf_path = {"main": exact_paper_path}  # Store as dict
                return exact_paper_path
            self.pdf_path = None  # Reset if no match found
            return ""

        # Import re only when searching in subdirectories (on-demand import)
        import re
        pattern = re.compile(re.escape(key_content), re.IGNORECASE)

        # Partial match for subdirectory search
        for file in os.listdir(search_path):
            if file.endswith(".pdf") and pattern.search(file):
                paper_path = os.path.join(search_path, file)
                self.pdf_path = {version: paper_path}  # Store as dict
                return paper_path

        self.pdf_path = None  # Reset if no match found
        return ""




    def open_pdf(self, version="main"):
        """Open the stored PDF file with the default viewer."""
        if not isinstance(self.pdf_path, dict) or version not in self.pdf_path:
            raise FileNotFoundError(f"No valid PDF file found for version: {version}.")

        pdf_to_open = self.pdf_path[version]
        if not os.path.isfile(pdf_to_open):
            raise FileNotFoundError(f"PDF file '{pdf_to_open}' does not exist.")

        if os.name == "nt":  # Windows
            os.startfile(pdf_to_open)
        elif os.name == "posix":  # macOS or Linux
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", pdf_to_open])
        else:
            raise OSError("Unsupported operating system.")
