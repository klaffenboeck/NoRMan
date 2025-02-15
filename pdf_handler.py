import os
import shutil
import subprocess
import sys

class PdfHandler:
    def __init__(self, papers_path):
        """Initialize the handler with the base path for storing PDFs."""
        self.papers_path = os.path.expanduser(papers_path)
        self.pdf_path = None

    def select_pdf_file(self, file_path):
        """Set the selected PDF file path if valid."""
        if file_path and os.path.isfile(file_path):
            self.pdf_path = file_path
            return self.pdf_path
        raise FileNotFoundError("Invalid file selected.")

    def rename_and_move_pdf(self, key_content):
        """Rename and move the selected PDF file."""
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
        self.pdf_path = destination_file
        return self.pdf_path

    def find_paper_path(self, key_content):
        """Check if a PDF with the given key_content exists in papers_path."""
        paper_path = os.path.join(self.papers_path, f"{key_content}.pdf")
        if os.path.exists(paper_path):
            self.pdf_path = paper_path
            return paper_path
        return ""

    def open_pdf(self):
        """Open the stored PDF file with the default viewer."""
        if not self.pdf_path or not os.path.isfile(self.pdf_path):
            raise FileNotFoundError("No valid PDF file to open.")

        if os.name == "nt":  # Windows
            os.startfile(self.pdf_path)
        elif os.name == "posix":  # macOS or Linux
            subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", self.pdf_path])
        else:
            raise OSError("Unsupported operating system.")
