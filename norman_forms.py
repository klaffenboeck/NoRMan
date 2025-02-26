import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkFont
import re
#import notion_paper
import os, sys
import shutil
import subprocess
import pprint
import bibtexparser
import json
import webbrowser
from notion import NotionAPI, NotionPage
from config_editor import ConfigEditor
from pdf_handler import PdfHandler
from citation_manager import CitationManager
from reference_manager import ReferenceManager
from multi_clipboard import ClipboardFactory
from preference_handler import PreferenceHandler
from key_handler import KeyHandler, AutocompleteCombobox


# Define the main application class
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure the main window
        self.title("Atop the RabbitHoles")
        self.geometry("400x350+5+5")

        self.config_path = "configs/config.json"
        self.config_data = self.load_config(self.config_path)
        # NOTE: notion_api has to be remove once changes are finished
        self.notion_api = NotionAPI()

        # Create a main container to hold everything
        main_container = tk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Create a toggle button to show/hide additional options
        self.toggle_button = ttk.Button(main_container, text="Show Options ▲", command=self.toggle_options)
        self.toggle_button.pack(fill=tk.X, padx=10)

        # Create a frame for additional buttons (initially hidden)
        self.options_frame = tk.Frame(main_container)
        self.options_visible = False  # Track visibility status

        # Move button_frame inside options_frame
        button_frame = tk.Frame(self.options_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.new_child_button = ttk.Button(button_frame, text="Open RabbitHole", command=self.new_child_window)
        self.new_child_button.pack(side=tk.LEFT, pady=5)

        self.open_editor_btn = tk.Button(button_frame, text="Edit Config", command=self.open_config_editor)
        self.open_editor_btn.pack(side=tk.LEFT, pady=5)

        # Add button to open the WindowListView
        self.open_list_view_button = ttk.Button(button_frame, text="List All", command=self.open_window_list_view)
        self.open_list_view_button.pack(side=tk.LEFT, pady=5)

        # Create a frame to hold the Treeview and Scrollbar
        frame = ttk.Frame(main_container)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add a vertical scrollbar
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add a treeview to display the window hierarchy
        self.tree = ttk.Treeview(frame, yscrollcommand=v_scrollbar.set)
        self.tree.heading("#0", text="Hierarchy of RabbitHoles", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)

        v_scrollbar.config(command=self.tree.yview)

        # Add the root node for the treeview
        self.tree.insert("", "end", iid="root", text="The Surface")
        self.tree.bind("<Double-1>", self.focus_window)

        self.child_count = 0
        self.total_descendant_count = 0

        self.project_options = self.config_data["project_options"]
        self.type_options = self.config_data["type_options"]
        self.venue_options = self.config_data["venue_options"]
        self.favorites = self.config_data["favorites"]
        self.favorite_citation_settings = self.favorites["citation_settings"]
        self.keyboard_shortcuts = self.config_data["keyboard_shortcuts"]
        self.clipboard = ClipboardFactory.get_clipboard()

        self.reload_config()

        self.windows = {"root": self}
        self.after(100, self.new_child_window)

    def open_window_list_view(self):
        WindowListView(self)


    def toggle_options(self):
        """Toggle the visibility of the options frame."""
        if self.options_visible:
            self.options_frame.pack_forget()
            self.toggle_button.config(text="Show Options ▲")
        else:
            self.options_frame.pack(fill=tk.X, padx=10, pady=5)
            self.toggle_button.config(text="Hide Options ▼")
        self.options_visible = not self.options_visible

    def load_config(self, file_path):
        """Load and return JSON configuration data."""
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                print(f"Loaded JSON data: {data}")
                return data
        except FileNotFoundError:
            print(f"Error: {file_path} not found.")
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in {file_path}.")
        return {}

    # TODO: config has to be loaded and reloaded through ConfigHandler
    def reload_config(self):
        self.config_data = self.load_config("configs/config.json")
        self.project_options = self.config_data["project_options"]
        self.type_options = self.config_data["type_options"]
        self.venue_options = self.config_data["venue_options"]
        self.formatting_styles = self.load_config("configs/formatting_styles.json")
        #print(f"self.formatting_styles type: {type(self.formatting_styles)}")
        self.journal_style_options = list(self.formatting_styles["journal_formatting_styles"].keys())
        self.journal_style_options.insert(0, "--style--")
        self.keyboard_shortcuts = self.config_data["keyboard_shortcuts"]

    def open_config_editor(self):
        """Opens the ConfigEditor as a subwindow."""
        ConfigEditor(self)


    def new_child_window(self):
        # Increment the child count
        self.child_count += 1

        # Create a new child window
        child = HierarchyWindow(self, self, f"Child Window {self.child_count}")

        # Add the child to the treeview
        self.tree.insert("root", "end", iid=f"Child Window {self.child_count}", text=f"Child Window {self.child_count}")

        # Store a reference to the child window
        self.windows[f"Child Window {self.child_count}"] = child

    def update_tree(self, parent_name, child_name, key):
        display_name = f"{key} ({child_name.split(' ', 1)[1]})"
        self.tree.item(child_name, text=display_name)

    def remove_from_tree(self, name):
        if name in self.windows:
            del self.windows[name]
            self.tree.delete(name)

    def focus_window(self, event):
        # Get the selected item
        selected_item = self.tree.selection()[0]

        # Retrieve the window reference and bring it to focus
        window = self.windows.get(selected_item)
        if window:
            window.lift()  # Bring the window to the front
            window.focus_force()  # Set focus to the window
            if isinstance(window, HierarchyWindow):
                window.key_entry.focus_set()  # Place the cursor in the key entry field

    def add_project_option(self, value):
        self.project_options.append(value)

    def add_venue_type_option(self, value):
        self.venue_options.append(value)

    def bring_to_front(self):
        """Bring main application window to the front."""
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))  # Reset topmost after a brief moment

    def copy_to_clipboard(self, value):
        self.clipboard.copy(value)
        # self.clipboard_clear()
        # self.clipboard_append(value)
        # self.update() # keep the clipboard content after application closes

def main():
    print("CALLED main()")
    app = MainApp()
    app.mainloop()

class WindowListView(tk.Toplevel):
    def __init__(self, main_app):
        super().__init__(main_app)
        self.main_app = main_app
        self.title("All RabbitHoles")
        self.geometry("400x400+50+50")

        # Create a frame for the Treeview and Scrollbar
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Add a vertical scrollbar
        v_scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Add a treeview to display the windows in alphabetical order
        self.tree = ttk.Treeview(frame, yscrollcommand=v_scrollbar.set)
        self.tree.heading("#0", text="Alphabetical RabbitHoles", anchor="w")
        self.tree.pack(fill=tk.BOTH, expand=True)

        v_scrollbar.config(command=self.tree.yview)

        # Populate the treeview with sorted window display names
        self.populate_tree()

        # Bind double-click event to focus the window
        self.tree.bind("<Double-1>", self.focus_window)

    def populate_tree(self):
        window_items = [(name, self.main_app.tree.item(name, 'text')) for name in self.main_app.windows.keys()]
        window_items.sort(key=lambda x: x[1])  # Sort by display names

        for name, display_name in window_items:
            self.tree.insert("", "end", iid=name, text=display_name)

    def focus_window(self, event):
        selected_item = self.tree.selection()[0]
        window = self.main_app.windows.get(selected_item)
        if window:
            window.lift()
            window.focus_force()
            if isinstance(window, HierarchyWindow):
                window.key_entry.focus_set()

# Define the hierarchy window class
class HierarchyWindow(tk.Toplevel):
    def __init__(self, main_app, parent, name):
        super().__init__(parent)

        # Track the name and number of subwindows
        self.main_app = main_app
        self.parent = parent
        self.name = name
        self.subwindow_count = 0
        main_app.total_descendant_count += 1
        self.authors = []
        self.notion_page_id = []
        self.sent_to_notion = False
        self.loaded_from_notion = False
        self.pdf_handler = PdfHandler(main_app.config_data["papers_path"])
        self.cm = CitationManager(main_app.config_path)
        self.refman = ReferenceManager()
        self.inherit_projects()
        self.key_handler = KeyHandler()

        # Bind the destroy event to your custom close logic
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        #self.bind("<Destroy>", self.on_destroy)

        # Configure the hierarchy window
        self.title(name)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 840
        window_height = 920
        counter_offset = (main_app.total_descendant_count * 20) % 400
        x_offset = (screen_width - window_width + counter_offset) // 2
        y_offset = (screen_height - window_height + counter_offset) // 2
        self.geometry(f"{window_width}x{window_height}+{x_offset}+{y_offset}")


        self.form_frame = ttk.Frame(self, padding=10)
        self.form_frame.grid(row=0, column=0, sticky="NSEW")

        # add project_tag label and combobox
        self.project_label = ttk.Label(self.form_frame, text="Project(s):")
        self.project_label.grid(row=1, column=0, padx=5, pady=5, sticky="E")
        self.project_combo = ttk.Combobox(self.form_frame, values=self.main_app.project_options, width=26)
        self.project_combo.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="W")


        self.projects_var = tk.StringVar()
        self.projects_label = ttk.Label(self.form_frame, font=("Arial", 10), textvariable=self.projects_var, background="white")
        self.projects_label.grid(row=1, column=1, columnspan=8, padx=9, pady=10, sticky="W")


        # Add papertrail label and entry
        self.papertrail_label = ttk.Label(self.form_frame, text="Papertrail:")
        self.papertrail_label.grid(row=1, column=3, padx= 5, pady=0, sticky="E")
        self.papertrail_var = tk.StringVar()
        if isinstance(parent,HierarchyWindow):
            self.papertrail_var = tk.StringVar(value=parent.key_entry.get())
        self.papertrail_entry = ttk.Entry(self.form_frame, textvariable=self.papertrail_var, width=23)
        self.papertrail_entry.grid(row=1, column=4, columnspan=3, padx=0, pady=5, sticky="W")
        self.papertrail_entry.bind("<KeyRelease>", lambda event: [self.update_reference("papertrail",self.papertrail_entry.get())])

        self.copy_papertrail_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.papertrail))
        self.copy_papertrail_btn.grid(row=1, column=7, padx=5, pady=0, sticky="W")

    # Add a horizontal separator
        self.separator = ttk.Separator(self.form_frame, orient="horizontal")
        self.separator.grid(row=3, column=0, columnspan=10, pady=5, sticky="ew")

        # Add label and entry for key
        self.key_label = ttk.Label(self.form_frame, text="Key:")
        self.key_label.grid(row=5, column=0, columnspan=1, padx=5, pady=5, sticky="E")
        self.key_var = tk.StringVar()
        #self.key_entry = ttk.Entry(self.form_frame, textvariable=self.key_var, width=23)
        self.key_entry = AutocompleteCombobox(self.form_frame, self.key_handler, textvariable=self.key_var, width=23)
        self.key_entry.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="W")
        #self.key_entry.bind("<KeyRelease>", lambda event: self.update_tree())
        self.key_entry.bind("<KeyRelease>", lambda event: [self.update_reference("key",self.key_entry.get()), self.update_tree(), self.key_entry._on_keyrelease(event)])
        self.key_entry.bind("<<ComboboxSelected>>", lambda event: [self.update_reference("key",self.key_entry.get()), self.load_reference()])

        self.validate_key_btn = ttk.Button(self.form_frame, text="Validate", command=self.validate_key, width=7)
        self.validate_key_btn.grid(row=5, column=5, padx=5, pady=5, sticky="W")
        self.key_validation = tk.StringVar()
        self.key_validation_label = ttk.Label(self.form_frame, font=("Lucida Console", 8), textvariable=self.key_validation)
        self.key_validation_label.grid(row=5, column=3, padx=0, pady=0, sticky="W")

        self.copy_key_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.key))
        self.copy_key_btn.grid(row=5, column=6, padx=5, pady=0, sticky="W")

        self.copy_keycite_btn = ttk.Button(self.form_frame, text="\\cite", command=lambda: self.cc(self.refman.keycite()))
        self.copy_keycite_btn.grid(row=5, column=7, padx=5, pady=0, sticky="W")

        self.key_project_combo = ttk.Combobox(self.form_frame, values=self.refman.project, width=7)
        self.key_project_combo.grid(row=6, column=5, pady=5, padx=5, sticky="W")
        self.key_project_combo.bind("<<ComboboxSelected>>", lambda event: [PreferenceHandler.set("curr_project",self.key_project_combo.get()),self.update_ui(), self.copy_key_project()])

        self.key_project_connector_combo = ttk.Combobox(self.form_frame, values=["_","-", " - "], justify="center", width=3)
        self.key_project_connector_combo.grid(row=6, column=3, pady=5, padx=5, sticky="E")
        self.key_project_connector_combo.set(PreferenceHandler.get("key_project_connector","_"))
        self.key_project_connector_combo.bind("<<ComboboxSelected>>", lambda event: [PreferenceHandler.set("key_project_connector",self.key_project_connector_combo.get()), self.copy_key_project()])

        self.copy_key_project_btn = ttk.Button(self.form_frame, text="Copy", command=self.copy_key_project)
        self.copy_key_project_btn.grid(row=6, column=6, padx=5, pady=0, sticky="W")

        # add bibtex label and entry
        self.bibtex_label = ttk.Label(self.form_frame, text="Bibtex:")
        self.bibtex_label.grid(row=20, column=0, columnspan=1, padx=5, pady=5, sticky="E")
        self.bibtex_field = tk.Text(self.form_frame, width=50, height=12, wrap="word")
        #self.bibtex_field.pack(pady=5, fill=tk.BOTH, padx=10, expand=True)
        self.bibtex_field.grid(row=20, column=1, columnspan=4, rowspan=7, padx=5, pady=5, sticky="W")
        self.bibtex_chars = tk.StringVar(value="0/2000")
        self.bibtex_chars_label = ttk.Label(self.form_frame, font=("Lucida Console", 5), textvariable=self.bibtex_chars)
        self.bibtex_chars_label.grid(row=24, column=0, padx=8, pady=8, sticky="SE")
        self.bibtex_field.bind("<KeyRelease>", lambda event: [self.update_reference("bibtex",self.get_fieldtext(self.bibtex_field))])

        self.second_bibtex_label = ttk.Label(self.form_frame, text="Bibtex cmds:")
        self.second_bibtex_label.grid(row=20, column=5, padx=5, pady=5, sticky="N")

        self.parse_bibtex_btn = ttk.Button(self.form_frame, text="Parse", command=lambda: self.update_reference("bibtex",self.gf(self.bibtex_field)), width=5)
        self.parse_bibtex_btn.grid(row=20, column=6, padx=5, pady=0, sticky="N")

        self.copy_bibtex_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.bibtex), width=5)
        self.copy_bibtex_btn.grid(row=20, column=7, padx=5, pady=0, sticky="N")

        # self.bibtex_radio_options = tk.StringVar(value="original")
        # self.bibtex_radio_btn1 = tk.Radiobutton(self.form_frame, text="original", variable=self.bibtex_radio_options, value="original", command=self.format_bibtex)
        # self.bibtex_radio_btn2 = tk.Radiobutton(self.form_frame, text="reformatted", variable=self.bibtex_radio_options, value="reformatted", command=self.format_bibtex)
        # self.bibtex_radio_btn3 = tk.Radiobutton(self.form_frame, text="reduced", variable=self.bibtex_radio_options, value="reduced", command=self.format_bibtex)

        # self.bibtex_radio_btn1.grid(row=21, column=5, padx=5, pady=5, sticky="w")
        # self.bibtex_radio_btn2.grid(row=21, column=6, padx=5, pady=5, sticky="w")
        # self.bibtex_radio_btn3.grid(row=21, column=7, padx=5, pady=5, sticky="w")

        self.citation_settings_label = ttk.Label(self.form_frame, text="Citation settings")
        self.citation_settings_label.grid(row=22, column=5, padx=5, pady=5, sticky="W")
        self.citation_separator = ttk.Separator(self.form_frame, orient="horizontal")
        self.citation_separator.grid(row=22, column=6, columnspan=2, pady=5, sticky="ew")

        self.citation_style_number1 = ttk.Label(self.form_frame, text="#1:")
        self.citation_style_number1.grid(row=23, column=5, padx=5, pady=5, sticky="W")

        self.citation_style_number1 = ttk.Label(self.form_frame, text="#1:")
        self.citation_style_number1.grid(row=23, column=5, padx=5, pady=5, sticky="W")
        self.citation_style_number2 = ttk.Label(self.form_frame, text="#2:")
        self.citation_style_number2.grid(row=24, column=5, padx=5, pady=5, sticky="W")


        self.cite_style1_combo = ttk.Combobox(self.form_frame, values=self.main_app.journal_style_options, width=7)
        self.cite_style1_combo.grid(row=23, column=5, pady=5, padx=(30, 5), sticky="W")
        self.cite_style1_combo.set(PreferenceHandler.get("cite_style1", "--style--"))

        self.cite_style2_combo = ttk.Combobox(self.form_frame, values=self.main_app.journal_style_options, width=7)
        self.cite_style2_combo.grid(row=24, column=5, pady=5, padx=(30, 5), sticky="W")
        self.cite_style2_combo.set(PreferenceHandler.get("cite_style2", "--style--"))

        self.cite_format1_combo = ttk.Combobox(self.form_frame, values=["--format--", "Plain", "HTML", "LaTeX", "Html+CSS", "Markdown", "RichText"], width=7)
        self.cite_format1_combo.grid(row=23, column=6, pady=5, padx=5, sticky="W")
        self.cite_format1_combo.set(PreferenceHandler.get("cite_format1", "--format--"))

        self.cite_format2_combo = ttk.Combobox(self.form_frame, values=["--format--", "Plain", "HTML", "LaTeX", "Html+CSS", "Markdown", "RichText"], width=7)
        self.cite_format2_combo.grid(row=24, column=6, pady=5, padx=5, sticky="W")
        self.cite_format2_combo.set(PreferenceHandler.get("cite_format2", "--format--"))

        self.cite_appendix1_combo = ttk.Combobox(self.form_frame, values=["-append-", "Link", "None"], width=7)
        self.cite_appendix1_combo.grid(row=23, column=7, pady=5, padx=5, sticky="W")
        self.cite_appendix1_combo.set(PreferenceHandler.get("cite_ref1", "-append-"))

        self.cite_appendix2_combo = ttk.Combobox(self.form_frame, values=["-append-", "Link", "None"], width=7)
        self.cite_appendix2_combo.grid(row=24, column=7, pady=5, padx=5, sticky="W")
        self.cite_appendix2_combo.set(PreferenceHandler.get("cite_ref2", "-append-"))

        # Bind the Combobox selection events to save preferences
        self.cite_style1_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_style1", self.cite_style1_combo.get()))
        self.cite_style2_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_style2", self.cite_style2_combo.get()))
        self.cite_format1_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_format1", self.cite_format1_combo.get()))
        self.cite_format2_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_format2", self.cite_format2_combo.get()))
        self.cite_appendix1_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_ref1", self.cite_appendix1_combo.get()))
        self.cite_appendix2_combo.bind("<<ComboboxSelected>>", lambda event: PreferenceHandler.set("cite_ref2", self.cite_appendix2_combo.get()))
        self.project_combo.bind("<<ComboboxSelected>>", lambda event: [PreferenceHandler.set("curr_project", self.project_combo.get()),self.update_reference("project",self.project_combo.get())])

        # Add year label and entry
        self.year_label = ttk.Label(self.form_frame, text="Year:")
        self.year_label.grid(row=27, column=2, padx=5, pady=5, sticky="E")
        self.year_var = tk.StringVar()
        self.year_entry = ttk.Entry(self.form_frame, textvariable=self.year_var, width=10)
        self.year_entry.grid(row=27, column=3, padx=5, pady=5, sticky="W")
        self.year_entry.bind("<KeyRelease>", lambda event: self.update_reference("year", str(self.year_var.get())))

        # Add citation count label and entry
        self.count_label = ttk.Label(self.form_frame, text="Cite-Count:")
        self.count_label.grid(row=27, column=0, padx=5, pady=5, sticky="E")
        validate_number = self.register(self.only_numbers)
        self.count_var = tk.StringVar()
        self.count_entry = ttk.Entry(self.form_frame, textvariable=self.count_var, validate="key", validatecommand=(validate_number, "%S"), width=10)
        self.count_entry.grid(row=27, column=1, padx=5, pady=5, sticky="W")
        self.count_entry.bind("<KeyRelease>", lambda event: self.update_reference("count", str(self.count_var.get())))

        self.refcite_label = tk.Label(self.form_frame, text="Copy reference:")
        self.refcite_label.grid(row=27, column=6, padx=0, pady=(5,10), sticky="E")

        self.refcite1_button = tk.Button(self.form_frame, text="#1", width=1, command=self.refcite1)
        self.refcite1_button.configure(relief="flat")
        self.refcite1_button.grid(row=27, column=7, padx=5, pady=(5,10), ipadx=0, ipady=0, sticky="W")
        self.refcite2_button = tk.Button(self.form_frame, text="#2", width=1, command=self.refcite2)
        self.refcite2_button.configure(relief="flat")
        self.refcite2_button.grid(row=27, column=7, padx=(45,0), pady=(5,10), ipadx=0, ipady=0, sticky="W")

        # add title label and entry
        self.title_label = ttk.Label(self.form_frame, text="Title:")
        self.title_label.grid(row=30, column=0, padx=5, pady=5, sticky="E")
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(self.form_frame, textvariable=self.title_var, width=38)
        self.title_entry.grid(row=30, column=1, columnspan=3, padx=5, pady=5, sticky="W")
        self.title_entry.bind("<KeyRelease>", lambda event: self.update_reference("title", str(self.title_var.get())))

        self.copy_title_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.title))
        self.copy_title_btn.grid(row=30, column=5, padx=5, pady=0, sticky="W")

        # self.cite_title_btn = ttk.Button(self.form_frame, text="\\cite", command=self.cite_title)
        # self.cite_title_btn.grid(row=30, column=6, padx=5, pady=0, sticky="W")

        self.short_title_label = ttk.Label(self.form_frame, text="Short title:")
        self.short_title_label.grid(row=31, column=0, padx=5, pady=5, sticky="E")
        self.short_title_var = tk.StringVar()
        self.short_title_entry = tk.Entry(self.form_frame, textvariable=self.short_title_var, width=25)
        self.short_title_entry.grid(row=31, column=1, columnspan=2, padx=5, pady=5, sticky="W")
        self.short_title_entry.bind("<KeyRelease>", lambda event: self.update_reference("short_title", str(self.short_title_var.get())))

        self.short_title_manual_bool = tk.BooleanVar()
        self.short_title_manual_checkbox = tk.Checkbutton(self.form_frame, variable=self.short_title_manual_bool, state="disabled")
        self.short_title_manual_checkbox.grid(row=31, column=3, padx=5, pady=5, sticky="E")

        self.short_title_length_var = tk.StringVar()
        self.short_title_length_options = list(map(str, list(range(25,51))))
        self.short_title_length_combo = ttk.Combobox(self.form_frame, values=self.short_title_length_options, width=3)
        self.short_title_length_combo.grid(row=31, column=3, padx=5, pady=5, sticky="W")
        self.short_title_length_combo.bind("<<ComboboxSelected>>", lambda event: [self.generate_short_title()])
        self.short_title_length_combo.bind("<Return>", lambda event: self.generate_short_title())

        self.copy_short_title_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.short_title_var.get()))
        self.copy_short_title_btn.grid(row=31, column=5, padx=5, pady=5, sticky="W")


        self.footcite_label = tk.Label(self.form_frame, text="Copy footnote:")
        self.footcite_label.grid(row=30, column=6, padx=0, pady=(5,10), sticky="E")

        self.footcite1_button = tk.Button(self.form_frame, text="#1", width=1, command=self.footcite1)
        self.footcite1_button.configure(relief="flat")
        self.footcite1_button.grid(row=30, column=7, padx=5, pady=(5,10), ipadx=0, ipady=0, sticky="W")
        self.footcite2_button = tk.Button(self.form_frame, text="#2", width=1, command=self.footcite2)
        self.footcite2_button.configure(relief="flat")
        self.footcite2_button.grid(row=30, column=7, padx=(45,0), pady=(5,10), ipadx=0, ipady=0, sticky="W")

        self.incite_label = tk.Label(self.form_frame, text="Copy in-text:")
        self.incite_label.grid(row=31, column=6, padx=0, pady=(5,10), sticky="E")
        self.incite1_button = tk.Button(self.form_frame, text="#1", width=1, command=self.incite1)
        self.incite1_button.configure(relief="flat")
        self.incite1_button.grid(row=31, column=7, padx=5, pady=(5,10), ipadx=0, ipady=0, sticky="W")
        self.incite2_button = tk.Button(self.form_frame, text="#2", width=1, command=self.incite2)
        self.incite2_button.configure(relief="flat")
        self.incite2_button.grid(row=31, column=7, padx=(45,0), pady=(5,10), ipadx=0, ipady=0, sticky="W")

        #small_default_font = tkFont.nametofont("TkDefaultFont")
        #small_default_font.configure(size=8)  # Change default size

        self.authors_label = ttk.Label(self.form_frame, text="Authors:", font=("Lucida Grande", 9))
        self.authors_label.grid(row=33, column=0, padx=5, pady=5, sticky="E")
        self.authors_var = tk.StringVar()
        self.authors_entry = tk.Entry(self.form_frame, textvariable=self.authors_var, width=57, font=("Lucida Grande", 7), state="readonly")
        self.authors_entry.grid(row=33, column=1, columnspan=3, padx=5, pady=5, ipady=1, sticky="W")
        #self.authors_entry.bind("<KeyRelease>", lambda event: self.parse_authors_entry())

        # self.action_options = ["-action-","copy","cite-#1", "cite-#2", "cite-global"]
        # self.authors_action_combo = ttk.Combobox(self.form_frame, values=self.action_options, width=7, state="readonly")
        # self.authors_action_combo.title = "authors_action"
        # self.authors_action_combo.grid(row=33, column=6, padx=5, pady=5, sticky="W")
        # self.authors_action_combo.set(self.authors_action_combo["values"][0])
        # #self.authors_action_combo.bind("<<ComboboxSelected>>", self.how_to_copy)



        # add abstract label and textfield
        self.abstract_label = ttk.Label(self.form_frame, text="Abstract:")
        self.abstract_label.grid(row=40, column=0, padx=5, pady=5, sticky="E")
        self.abstract_field = tk.Text(self.form_frame, width=50, height=5, wrap="word")
        self.abstract_field.grid(row=40, column=1, columnspan=4, padx=5, pady=5, sticky="W")
        self.abstract_chars = tk.StringVar(value="0/2000")
        self.abstract_chars_label = ttk.Label(self.form_frame, font=("Lucida Console", 5), textvariable=self.abstract_chars)
        self.abstract_chars_label.grid(row=40, column=0, padx=8, pady=8, sticky="SE")
        self.abstract_field.bind("<KeyRelease>", lambda event: [self.update_reference("abstract",self.get_fieldtext(self.abstract_field))])

        self.copy_abstract_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.abstract))
        self.copy_abstract_btn.grid(row=40, column=5, padx=5, pady=0, sticky="W")

        # add journal label and entry
        self.journal_label = ttk.Label(self.form_frame, text="Journal:")
        self.journal_label.grid(row=50, column=0, padx=5, pady=5, sticky="E")
        self.journal_var = tk.StringVar()
        self.journal_entry = tk.Entry(self.form_frame, textvariable=self.journal_var, width=38)
        self.journal_entry.grid(row=50, column=1, columnspan=3, padx=5, pady=5, sticky="W")
        self.journal_entry.bind("<KeyRelease>", lambda event: self.update_reference("journal", str(self.journal_var.get())))

        # Add pub type label and options
        self.type_label = ttk.Label(self.form_frame, text="Pub-Type:")
        self.type_label.grid(row=55, column=2, padx=5, pady=5, sticky="E")
        self.type_combo = ttk.Combobox(self.form_frame, values=self.main_app.type_options, width=7)
        self.type_combo.set(self.main_app.type_options[0])
        self.type_combo.grid(row=55, column=3, padx=5, pady=5, sticky="W")
        self.type_combo.bind("<<ComboboxSelected>>", lambda event: [self.update_reference("type", self.type_combo.get())])

        # Add venue label and options
        self.venue_label = ttk.Label(self.form_frame, text="Venue:")
        self.venue_label.grid(row=55, column=0, padx=5, pady=5, sticky="E")
        self.venue_combo = ttk.Combobox(self.form_frame, values=self.main_app.venue_options, width=10)
        #self.venue_combo.set(self.main_app.venue_options[0])
        self.venue_combo.grid(row=55, column=1, padx=5, pady=5, sticky="W")

        # add link_doi label and entry
        self.link_doi_label = ttk.Label(self.form_frame, text="Link/DOI:", font=("Lucida Grande", 9))
        self.link_doi_label.grid(row=70, column=0, padx=5, pady=5, sticky="E")
        self.link_doi_var = tk.StringVar()
        self.link_doi_entry = ttk.Entry(self.form_frame, textvariable=self.link_doi_var, width=57, font=("Lucida Grande", 7))
        self.link_doi_entry.grid(row=70, column=1, columnspan=3, padx=5, pady=5, ipady=1, sticky="W")

        # add open link_doi button
        self.copy_link_doi_btn = ttk.Button(self.form_frame, text="Copy", command=self.copy_link_doi)
        self.copy_link_doi_btn.grid(row=70, column=5, padx=5, pady=0, sticky="W")

        # add open link_doi button
        self.open_link_doi_btn = ttk.Button(self.form_frame, text="Open", command=self.open_link_doi)
        self.open_link_doi_btn.grid(row=70, column=6, padx=5, pady=0, sticky="W")

        # add notes label and textfield
        self.notes_label = ttk.Label(self.form_frame, text="Notes:")
        self.notes_label.grid(row=80, column=0, padx=5, pady=5, sticky="E")
        self.notes_field = tk.Text(self.form_frame, width=50, height=5, wrap="word")
        self.notes_field.grid(row=80, column=1, columnspan=4, padx=5, pady=5, sticky="W")
        self.notes_chars = tk.StringVar(value="0/2000")
        self.notes_chars_label = ttk.Label(self.form_frame, font=("Lucida Console", 5), textvariable=self.notes_chars)
        self.notes_chars_label.grid(row=80, column=0, padx=8, pady=8, sticky="SE")
        self.notes_field.bind("<KeyRelease>", lambda event: [self.update_reference("notes",self.gf(self.notes_field))])

        self.copy_notes_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.cc(self.refman.notes))
        self.copy_notes_btn.grid(row=80, column=5, padx=5, pady=0, sticky="W")

        send_button_style = ttk.Style()
        send_button_style.configure("Custom.TButton", background="white", bordercolor="red", borderwidth=2)

        self.send_button = ttk.Button(self.form_frame, text="Send to Notion", command=self.save_reference, style="Custom.TButton",  width=15)
        self.send_button.grid(row=80, column=6, columnspan=2, padx=5, pady=5, sticky="SW")

        # Add a horizontal separator
        self.separator_pdf = ttk.Separator(self.form_frame, orient="horizontal")
        self.separator_pdf.grid(row=89, column=0, columnspan=10, pady=10, sticky="ew")

        # Add a label and entry for "PDF"
        self.pdf_label = ttk.Label(self.form_frame, text="Main PDF:")
        self.pdf_label.grid(row=90, column=0,  padx=5, pady=5, sticky="E")

        self.pdf_var = tk.StringVar()
        self.pdf_entry = ttk.Entry(self.form_frame, textvariable=self.pdf_var, width=38, state="readonly")
        self.pdf_entry.grid(row=90, column=1, columnspan=3, padx=5, pady=5, sticky="W")

        # Add a button to select a PDF file
        self.pdf_button = ttk.Button(self.form_frame, text="Select", command=self.select_pdf_file)
        self.pdf_button.grid(row=90, column=5, padx=5, pady=5, sticky="W")

        # Add a button to rename and move the PDF file
        self.rename_move_button = ttk.Button(self.form_frame, text="Move", command=self.rename_and_move_pdf)
        self.rename_move_button.grid(row=90, column=6, padx=5, pady=5, sticky="W")

        # Add a button to open the PDF file
        self.open_pdf_button = ttk.Button(self.form_frame, text="Open", command=self.open_pdf)
        self.open_pdf_button.grid(row=90, column=7, padx=5, pady=5, sticky="W")


        self.pdf2_label = ttk.Label(self.form_frame, text="Project PDF:")
        self.pdf2_label.grid(row=91, column=0,  padx=5, pady=5, sticky="E")

        self.pdf2_var = tk.StringVar()
        self.pdf2_entry = ttk.Entry(self.form_frame, textvariable=self.pdf2_var, width=38, state="readonly")
        self.pdf2_entry.grid(row=91, column=1, columnspan=3, padx=5, pady=5, sticky="W")

        self.pdf_project_combo = ttk.Combobox(self.form_frame, values=self.refman.project, width=7)
        self.pdf_project_combo.grid(row=91, column=5, pady=5, padx=5, sticky="W")
        self.pdf_project_combo.bind("<<ComboboxSelected>>", lambda event: [PreferenceHandler.set("curr_project",self.pdf_project_combo.get()),self.update_ui()])


        # Add a button to rename and move the PDF file
        self.rename_move2_button = ttk.Button(self.form_frame, text="Duplicate", command=self.duplicate_main_pdf)
        self.rename_move2_button.grid(row=91, column=6, padx=5, pady=5, sticky="W")

        # Add a button to open the PDF file
        self.open_pdf2_button = ttk.Button(self.form_frame, text="Open", command=self.open_project_pdf)
        self.open_pdf2_button.grid(row=91, column=7, padx=5, pady=5, sticky="W")

        # Add a button to save the form input
        # self.save_button = ttk.Button(self.form_frame, text="Save", command=self.save_form)
        # self.save_button.pack(pady=10)

        # Add a horizontal separator
        self.separator_btns = ttk.Separator(self.form_frame, orient="horizontal")
        self.separator_btns.grid(row=99, column=0, columnspan=10, pady=10, sticky="ew")

        # Add a button to create subwindows
        self.new_subwindow_button = ttk.Button(self.form_frame, text="New Child", command=self.new_subwindow)
        self.new_subwindow_button.grid(row=100, column=2, padx= 5, pady=5, sticky="W")

        # Add a button to create subwindows
        self.new_siblingwindow_button = ttk.Button(self.form_frame, text="New Sibling", command=self.new_siblingwindow)
        self.new_siblingwindow_button.grid(row=100, column=1, padx= 5, pady=5, sticky="W")

        # Add a button to close the window
        self.close_button = ttk.Button(self.form_frame, text="Close", command=self.close_window)
        self.close_button.grid(row=101, column=7, padx= 5, pady=5, sticky="W")

        # Add a button to close the window
        self.clear_button = ttk.Button(self.form_frame, text="Clear", command=self.clear_fields)
        self.clear_button.grid(row=100, column=7, padx= 5, pady=5, sticky="W")

        # Add a button to close the window
        self.reload_config_button = ttk.Button(self.form_frame, text="Reload config", command=self.reload_config)
        self.reload_config_button.grid(row=100, column=5, columnspan=2, padx= 5, pady=5, sticky="W")

        # Add a go to surface button
        self.go_to_surface_button = ttk.Button(self.form_frame, text="Go to surface", command=self.main_app.bring_to_front)
        self.go_to_surface_button.grid(row=101, column=1, padx= 5, pady=5, sticky="W")

        # Add a go to parent button
        self.go_to_surface_button = ttk.Button(self.form_frame, text="Go to parent", command=self.parent.bring_to_front)
        self.go_to_surface_button.grid(row=101, column=2, padx= 5, pady=5, sticky="W")

        self.parsed_bibtex = 0
        self.bibtex_url = ""
        self.bibtex_doi = ""
        self.is_waiting = False
        self.dots = 0
        self.sent_flag = False

        # # Bind Option (Alt) or Command key for dynamic change
        # self.bind("<KeyPress-Option_L>", lambda event: self.switch_to_load)  # macOS Option Key
        # self.bind("<KeyRelease-Option_L>", lambda event: self.switch_to_validate)

        # self.bind_all("<KeyPress-Alt_L>", lambda event: self.switch_to_load())  # Windows/Linux Alt Key
        # self.bind_all("<KeyRelease-Alt_L>", lambda event:  self.switch_to_validate())
        # self.bind_all("<Command-n>", lambda event: self.new_subwindow())  # macOS
        # self.bind_all("<Command-N>", lambda event: self.new_siblingwindow())  # macOS
        # self.bind_all("<Command-l>", lambda event: self.load_reference())  # macOS
        # self.bind_all("<Command-s>", lambda event: self.save_reference())  # macOS

        # # For Windows/Linux (Ctrl instead of Command)
        # self.bind_all("<Control-n>", lambda event: self.new_subwindow())
        # self.bind_all("<Control-N>", lambda event: self.new_siblingwindow())
        # self.bind_all("<Control-l>", lambda event: self.load_reference())
        # self.bind_all("<Control-s>", lambda event: self.save_reference())

        # # macOS: Bind Command+U to remove key
        # self.bind_all("<Command-U>", lambda event: self.remove_selected_key())

        # # Windows/Linux: Bind Control+U to remove key
        # self.bind_all("<Control-U>", lambda event: self.remove_selected_key())
        #
        keyboard_shortcuts = self.main_app.keyboard_shortcuts  # Retrieve shortcuts from MainApp

        for action, bindings in keyboard_shortcuts.items():
            target = bindings.pop("target", "self")  # Default to "self" if no target is specified

            for platform, shortcut in bindings.items():
                if (platform == "Windows/Linux" and not sys.platform.startswith("darwin")) or \
                (platform == "macOS" and sys.platform.startswith("darwin")):

                    target_obj = self if target == "self" else self.refman  # Default to self, unless target is "refman"

                    if not shortcut:  # Skip if shortcut is missing
                        continue

                    print(f"Binding {shortcut} to {action} on {target_obj}")  # Debugging output

                    try:
                        if "Option_L" in shortcut and sys.platform.startswith("darwin"):
                            self.bind(shortcut, lambda event, action=action, target_obj=target_obj: getattr(target_obj, action)())
                        else:
                            self.bind_all(shortcut, lambda event, action=action, target_obj=target_obj: getattr(target_obj, action)())
                    except tk.TclError as e:
                        print(f"Skipping invalid shortcut {shortcut}: {e}")



        #self.bind("<KeyRelease-Alt_L>", lambda event: self.switch_to_validate)

        # # If you want Command (⌘) key on macOS:
        # self.bind("<KeyPress-Command_L>", lambda event: self.switch_to_load)
        # self.bind("<KeyRelease-Command_L>", lambda event: self.switch_to_validate)
        #
        # self.bind("<Command_L>", lambda event: self.switch_to_load)
        # self.bind("<KeyRelease-Meta_L>", lambda event: self.switch_to_validate)
        #
        #self.bind("<KeyPress>", lambda event: print(f"Pressed: {event.keysym}"))
        self.form_frame.after(100, self.key_entry.focus_set)

        # Add this window to the main app's window reference
        self.main_app.windows[self.name] = self
        self.update_ui()

    def update_reference(self, key, value):
        #print(f"UPDATE_REFERENCE.{key} = {value}")
        setattr(self.refman, key, value)
        self.update_ui()

    ur = update_reference

    def get_citation(self):
        print(self.cm.process_citation(style="IEEE"))
        #print("NOT IMPLEMENTED YET")

    def refcite1(self):
        self.cite1("reference")

    def footcite1(self):
        self.cite1("footnote")

    def incite1(self):
        self.cite1("in-text")

    def refcite2(self):
         self.cite2("reference")

    def footcite2(self):
        self.cite2("footnote")

    def incite2(self):
        self.cite2("in-text")

    def cite1(self, type):
        style = self.cite_style1_combo.get()
        format = self.cite_format1_combo.get()
        append = self.cite_appendix1_combo.get()
        self.cc(self.refman.cite(style=style, formatter=format, type=type, appendix=append))

    def cite2(self, type):
        style = self.cite_style2_combo.get()
        format = self.cite_format2_combo.get()
        append = self.cite_appendix2_combo.get()
        self.cc(self.refman.cite(style=style, formatter=format, type=type, appendix=append))

    def inherit_projects(self):
        if isinstance(self.parent,HierarchyWindow):
            self.refman.project = self.parent.refman.project.copy()
        # else:
        #     self.projects = []

    def add_or_remove_project(self, project = ""):
        if not project:
            project = self.project_combo.get()

        if project in self.projects:
            self.projects.remove(project)  # Remove if it exists
            #print(f"Removed: {project}")
        else:
            self.projects.append(project)  # Add if it's not in the list
            #print(f"Added: {project}")

        # Optional: Update UI or Label if needed
        self.projects_var.set("; ".join(self.projects))  # Assuming projects_var is a StringVar
        self.project_combo.set("")

    def clear_projects(self):
        self.projects.clear()

    def switch_to_load(self):
        """Switch button to 'Load' mode when modifier key is pressed"""
        self.validate_key_btn.config(text="Load", command=self.load_reference, width=8)
        #self.send_button.config(text="Update in Notion", command=self.update_notion_entry, width=15)

    def switch_to_validate(self):
        """Switch button back to 'Validate' mode when modifier key is released"""
        self.validate_key_btn.config(text="Validate", command=self.validate_key, width=8)
        #self.send_button.config(text="Send to Notion", command=self.send_data_to_notion,  width=15)

    def get_fieldtext(self, field):
        return field.get("1.0",tk.END)

    gf = get_textfield = get_fieldtext

    def load_reference(self):
        self.refman.load_reference()
        self.cache_key()
        self.update_ui()

    def save_reference(self):
        self.refman.save_reference()

    def generate_short_title(self):
        length = int(self.short_title_length_combo.get())
        self.refman.short_title = self.refman.create_short_title(length)
        self.refman.short_title_manual = False
        self.update_ui()

    def update_ui(self):
        page = self.refman

        self.update_textfield(self.bibtex_field, page.bibtex)
        self.update_textfield(self.abstract_field, page.abstract)
        self.update_textfield(self.notes_field, page.notes)
        self.title_var.set(page.title)
        self.short_title_var.set(page.short_title)
        self.short_title_manual_bool.set(self.value_or_default(page.short_title_manual, False))
        if page.authors:
            self.authors = page.authors.to_string(" and ")
            self.authors_var.set(self.authors)
        else:
            self.authors_var.set("")
        self.journal_var.set(page.journal)
        self.venue_combo.set(page.venue)
        self.year_var.set(self.value_or_default(page.year, ""))
        self.count_var.set(self.value_or_default(page.count, ""))# if page.count else self.count_var.set("0")
        self.pdf_var.set(self.pdf_handler.find_paper_path(page.key))

        project_pdf = self.pdf_project_combo.get() if self.pdf_project_combo.get() else ""
        if project_pdf:
            self.pdf2_var.set(self.pdf_handler.find_paper_path(page.key, version=project_pdf))
        else:
            self.pdf2_var.set("")
        self.link_doi_var.set(page.reference.link_doi)
        self.papertrail_var.set(page.papertrail)
        self.projects_var.set("; ".join(self.refman.project))
        self.project_combo.set("")
        self.pdf_project_combo['values'] = self.refman.project
        self.key_project_combo['values'] = self.refman.project
        self.confirm_project_preference()

        self.pdf_project_combo.set(PreferenceHandler.get("curr_project",""))
        self.key_project_combo.set(PreferenceHandler.get("curr_project",""))
        if not self.refman.venue:
            self.ui_based_venue_mapping()
        if page.type:
            self.type_combo.set(page.type)
        #self.set_link_doi()
        self.update_counters()

    def confirm_project_preference(self):
        proj = PreferenceHandler.get("curr_project")
        if proj in self.refman.project:
            PreferenceHandler.set("curr_project", proj)
        else:
            PreferenceHandler.set("curr_project", "")

    def ui_based_venue_mapping(self):
        if not self.refman.venue:
            self.refman.venue = self.match_venue()

    def update_textfield(self, text_widget, text):
        cursor_pos = text_widget.index(tk.INSERT)

        # Simulate refreshing (clear and reinsert text)
        text_widget.delete("1.0", tk.END)
        text_widget.insert("1.0", text)

        # Restore cursor position
        text_widget.mark_set(tk.INSERT, cursor_pos)
        text_widget.see(tk.INSERT)  # Ensure it's visible

    utf = update_textfield

    def value_or_default(self, value, default):
        return value if value else default

    def copy_to_clipboard(self, value):
        self.main_app.copy_to_clipboard(value)

    cc = copy_to_clipboard

    def update_counters(self):
        self.update_bibtex_chars()
        self.update_abstract_chars()
        self.update_notes_chars()

    def update_bibtex_chars(self):
        count = len(self.bibtex_field.get("1.0", tk.END))
        self.bibtex_chars.set(f"{count}/2000")

    def update_abstract_chars(self):
        count = len(self.abstract_field.get("1.0", tk.END))
        self.abstract_chars.set(f"{count}/2000")

    def update_notes_chars(self):
        count = len(self.notes_field.get("1.0", tk.END))
        self.notes_chars.set(f"{count}/2000")

    def copy_title(self):
        value = self.title_var.get()
        self.main_app.copy_to_clipboard(value)

    def copy_key_project(self):
        key = self.refman.key
        conn = self.key_project_connector_combo.get()
        conn = conn if conn else ""
        proj = PreferenceHandler.get("curr_project","")
        val = (key+conn+proj)
        self.cc(val)
        return val

    def cite_title(self):
        value = self.title_var.get()
        key = self.key_var.get()
        self.main_app.copy_to_clipboard("\\emph{"+value + "} \\cite{"+key+"}")

    def fullcite_title(self):
        value = self.title_var.get()
        key = self.key_var.get()
        self.main_app.copy_to_clipboard("["+key+"] \\emph{"+value + "} \\cite{"+key+"}")

    def copy_link_doi(self):
        value = self.link_doi_var.get()
        self.main_app.copy_to_clipboard(value)

    def parse_bibtex(self):
        self.refman.bibtex = self.bibtex_field.get("1.0", tk.END).strip()
        self.update_ui()

    # TODO: format_bibtex (for radiobuttons) should be implemented in ReferenceManager
    def format_bibtex(self):
        pass
    #     cmd = self.bibtex_radio_options.get()
    #     print(cmd)
    #     f = self.cm.bibtex_formatter
    #     m = getattr(f, cmd, None)
    #     if m:
    #         self.bibtex_field.delete("1.0",tk.END)
    #         self.bibtex_field.insert("1.0", m())
    #     else:
    #         raise ValueError(f"Invalid method: {m}")

    def set_link_doi(self):
        if self.bibtex_url:
            self.link_doi_var.set(self.bibtex_url)
            return
        if self.bibtex_doi:
            match = re.search(r"(?:doi\.org/|^/)(.+)", self.bibtex_doi)
            if match:
                self.link_doi_var.set("https:/doi.org/"+match.group(1))
            else:
                self.link_doi_var.set("https:/doi.org/"+self.bibtex_doi)

    def open_link_doi(self):
        url = self.link_doi_var.get()
        webbrowser.open(url)  # Replace with your URL

    def parse_bibtex_authors(self):
        temp_authors = [author.strip().split(", ") for author in self.bibtex_authors.split(" and ")]
        self.authors = [(" ".join(reversed(name)) if len(name) > 1 else name[0]) for name in temp_authors]
        self.set_authors_var()
        #pprint.pprint(self.authors)

    def parse_authors_entry(self):
        authors = self.authors_entry.get()
        self.authors.clear()
        for author in authors.split(","):
            self.authors.append(author)

    def set_authors_var(self):
        self.authors_var.set(", ".join(self.authors))

    def match_venue(self):
        """Matches journal name against venue_mapping regex and sets the venue_combo value."""
        journal_name = self.journal_var.get()
        for mapping in self.main_app.config_data.get("venue_mapping", []):  # Ensure venue_mapping exists
            pattern = mapping.get("regex", "")
            venue = mapping.get("venue-mapping", "")
            if pattern and re.search(pattern, journal_name, re.IGNORECASE):  # Case-insensitive match

                self.venue_combo.set(venue)
                return venue# Stop after the first match

        # If no match is found, clear or set a default
        self.venue_combo.set("")
        return ""

    def validate_key(self):
        self.update_key_validation()


    def update_key_validation(self):
        self.is_waiting = True
        if self.check_key():
            self.is_waiting = False
            self.key_validation.set("is available")
            self.key_validation_label.config(foreground="green")
            self.update_bibtex_key()
        else:
            self.is_waiting = False
            self.key_validation.set("is NOT available!!")
            self.key_validation_label.config(foreground="red")
            self.cache_key()

    def check_key(self):
        title = self.key_entry.get()
        return self.main_app.notion_api.validate_key_availability(title)
        # LEFTOVER: loaded_from_notion in UI should not be necessary anymore.
        self.loaded_from_notion = True

    def cache_key(self):
        """Save the entered key to KeyHandler if it's new."""
        key = self.key_entry.get().strip()
        if key:
            self.key_handler.add_key(key)  # Save key to JSON
            self.key_entry["values"] = self.key_handler.get_keys()  # Refresh dropdown

    def remove_selected_key(self):
        """Remove the currently entered key from KeyHandler."""
        key = self.key_entry.get().strip()
        print(f"Attempting to remove key: '{key}'")  # Debugging statement
        if key:
            self.key_handler.remove_key(key)
            print(f"Key list after removal: {self.key_handler.get_keys()}")  # Debugging statement
            self.key_entry["values"] = self.key_handler.get_keys()  # Refresh dropdown
            self.key_entry.set("")  # Clear input field



    def only_numbers(self, char):
        # Return True if the input is a digit or empty (to allow deleting).
        return char.isdigit() or char == ""


    def update_tree(self):
        key = self.key_entry.get()
        #text = self.text_field.get("1.0", tk.END).strip()
        #print(f"Key: {key}, Text: {text}")
        # Determine the parent's name for updating the tree
        parent_name = self.parent.name if isinstance(self.parent, HierarchyWindow) else "root"

        # Update the treeview to show the key
        self.main_app.update_tree(parent_name, self.name, key)
        self.title(f"{key} ({self.name})")


    def get_bibtex_field(self):
        return self.bibtex_field.get("1.0", tk.END).strip()

    def get_abstract_field(self):
        return self.abstract_field.get("1.0", tk.END).strip()

    def get_notes_field(self):
        return self.notes_field.get("1.0", tk.END).strip()

    def get_text_field(self, field):
        return field.get("1.0", tk.END).strip()


    def select_pdf_file(self):
        """Handle UI interaction for selecting a PDF."""
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            try:
                selected_pdf = self.pdf_handler.select_pdf_file(file_path)
                self.pdf_var.set(selected_pdf)
            except FileNotFoundError:
                messagebox.showerror("Error", "Invalid file selected.")


    def rename_and_move_pdf(self):

        """Handle UI interaction for renaming/moving PDF."""
        key_content = self.refman.key
        try:
            new_path = self.pdf_handler.rename_and_move_pdf(key_content)
            self.pdf_var.set(new_path)
        except (ValueError, FileNotFoundError, FileExistsError) as e:
            messagebox.showerror("Error", str(e))

    def duplicate_main_pdf(self):
        project = self.pdf_project_combo.get()
        try:
            project_pdf_path = self.pdf_handler.duplicate(project, append=f"_{project}")
            self.pdf2_var.set(project_pdf_path)
        except (ValueError, FileNotFoundError, FileExistsError) as e:
            messagebox.showerror("Error", str(e))

    def open_pdf(self, version=""):
        print("NEW METHOD IS CALLED FOR OPENING")
        """Handle UI interaction for opening the PDF."""
        try:
            self.pdf_handler.open_pdf(version) if version else self.pdf_handler.open_pdf()
        except (FileNotFoundError, OSError) as e:
            messagebox.showerror("Error", str(e))

    def open_project_pdf(self):
        project = self.pdf_project_combo.get()
        self.open_pdf(project)

    def clear_fields(self):
        self.refman = ReferenceManager()
        self.update_ui()


    def confirm_with_ok_cancel(self):
        response = messagebox.askokcancel("Confirmation", "Are you sure? You haven't sent it yet...")
        if response:  # User clicked 'OK'
            self.clear_fields()
        else:  # User clicked 'Cancel'
            print("User canceled the action.")

    def new_subwindow(self):
        # Increment the subwindow count
        self.subwindow_count += 1

        # Create a new subwindow with a hierarchical name
        new_name = f"{self.name}-{self.subwindow_count}"
        subwindow = HierarchyWindow(self.main_app, self, new_name)

        # Add the subwindow to the treeview
        self.main_app.tree.insert(self.name, "end", iid=new_name, text=new_name)

        # Store a reference to the subwindow
        self.main_app.windows[new_name] = subwindow

    def new_siblingwindow(self):
        if isinstance(self.parent,HierarchyWindow):
            self.parent.new_subwindow()
        else:
            self.main_app.new_child_window()

    def bring_to_front(self):
        """Bring main application window to the front."""
        self.lift()
        self.focus_force()
        self.attributes('-topmost', True)
        self.after(100, lambda: self.attributes('-topmost', False))  # Reset topmost after a brief moment

    def reload_config(self):
        self.main_app.reload_config()
        self.type_combo["values"] = self.main_app.config_data["type_options"]
        self.project_combo["values"] = self.main_app.config_data["project_options"]
        self.venue_combo["values"] = self.main_app.config_data["venue_options"]

    def remove_children(self, node):
        children = self.main_app.tree.get_children(node)
        for child in children:
            self.remove_children(child)
            self.main_app.remove_from_tree(child)

    def close_window(self):
        # Remove this window and its children from the tree
        self.remove_children(self.name)
        self.main_app.remove_from_tree(self.name)
        # Destroy the window
        self.destroy()

    # def on_destroy(self, event=None):
    #     print(f"Window {self.name} destroyed")

if __name__ == "__main__":
    # Create and run the main application
    # app = MainApp()
    # app.mainloop()
    main()
