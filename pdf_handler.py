import os
import shutil
import subprocess
import sys
import re

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
        return self.pdf_path["main"]

    def duplicate(self, folder, **kwargs):
        """Duplicate the main PDF file into the _Projects/{folder} inside papers_path."""
        if not isinstance(self.pdf_path, dict) or "main" not in self.pdf_path:
            raise FileNotFoundError("Main PDF file does not exist or is not set.")

        main_pdf = self.pdf_path["main"]
        if not os.path.isfile(main_pdf):
            raise FileNotFoundError(f"Main PDF file '{main_pdf}' does not exist.")

        # ✅ New project path inside "_Projects/"
        destination_folder = os.path.join(self.papers_path, "_Projects", folder)
        os.makedirs(destination_folder, exist_ok=True)  # ✅ Ensure _Projects and project folder exist

        filename = os.path.basename(main_pdf)
        base_name, ext = os.path.splitext(filename)

        prepend = kwargs.get("prepend", "")
        append = kwargs.get("append", "")

        new_filename = f"{prepend}{base_name}{append}{ext}"
        new_pdf_path = os.path.join(destination_folder, new_filename)

        shutil.copy2(main_pdf, new_pdf_path)

        # Store the new file path in self.pdf_path
        if not isinstance(self.pdf_path, dict):
            self.pdf_path = {}

        self.pdf_path[folder] = new_pdf_path  # ✅ Store project PDF in new structure
        print(f"DEBUG: Copied to {new_pdf_path}")  # Debugging
        relative_path = os.path.relpath(new_pdf_path, self.papers_path)

        return relative_path

    def find_paper_path(self, key_content, version="main"):
        """Find a PDF file based on key_content inside the specified version folder.

        - Main PDFs are stored in `Papers/`
        - Project PDFs are stored in `Papers/_Projects/{project_name}/`
        """
        #print(f"DEBUG: Searching for {key_content}.pdf in {version}")  # Debugging

        if not version:
            return ""

        # ✅ Update search path for projects to `_Projects/{project_name}/`
        search_path = (
            self.papers_path if version == "main"
            else os.path.join(self.papers_path, "_Projects", version)
        )

        if not os.path.isdir(search_path):
            #print(f"DEBUG: Directory {search_path} does not exist")  # Debugging
            return ""

        if self.pdf_path is None:
            self.pdf_path = {}

        # ✅ **Main directory → Exact match only**
        if version == "main":
            exact_paper_path = os.path.join(search_path, f"{key_content}.pdf")
            if os.path.exists(exact_paper_path):
                self.pdf_path[version] = exact_paper_path
                relative_path = os.path.relpath(exact_paper_path, self.papers_path)
                print(f"DEBUG: Found exact match in main: {relative_path}")  # Debugging
                return relative_path

            #print(f"DEBUG: No exact match found in main for {key_content}.pdf")  # Debugging
            return ""

        # ✅ **Project directory → Allow partial matches**
        print(f"DEBUG: Looking for partial match in {search_path}")  # Debugging
        import re
        pattern = re.compile(re.escape(key_content), re.IGNORECASE)

        for file in os.listdir(search_path):
            if file.endswith(".pdf") and pattern.search(file):
                paper_path = os.path.join(search_path, file)
                self.pdf_path[version] = paper_path
                relative_path = os.path.relpath(paper_path, self.papers_path)
                print(f"DEBUG: Found partial match in {version}: {relative_path}")  # Debugging
                return relative_path

        #print(f"DEBUG: No match found for {key_content} in {search_path}")  # Debugging
        return ""


    def open_pdf(self, version="main"):
        """Open the stored PDF file with the default viewer."""
        #breakpoint()
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
