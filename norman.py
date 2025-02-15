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


# Define the main application class
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()

        # Configure the main window
        self.title("Atop the RabbitHoles")
        self.geometry("400x350+5+5")

        self.config_path = "configs/config.json"
        self.config_data = self.load_config(self.config_path)
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

    def reload_config(self):
        self.config_data = self.load_config("configs/config.json")
        self.project_options = self.config_data["project_options"]
        self.type_options = self.config_data["type_options"]
        self.venue_options = self.config_data["venue_options"]
        self.formatting_styles = self.load_config("configs/formatting_styles.json")
        #print(f"self.formatting_styles type: {type(self.formatting_styles)}")
        self.journal_style_options = list(self.formatting_styles["journal_formatting_styles"].keys())
        self.journal_style_options.insert(0, "--style--")

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
        self.clipboard_clear()
        self.clipboard_append(value)
        self.update() # keep the clipboard content after application closes


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
        self.inherit_projects()
        self.authors = []
        self.notion_page_id = []
        self.sent_to_notion = False
        self.loaded_from_notion = False
        self.pdf_handler = PdfHandler(main_app.config_data["papers_path"])
        self.cm = CitationManager(main_app.config_path)

        # Bind the destroy event to your custom close logic
        self.protocol("WM_DELETE_WINDOW", self.close_window)
        #self.bind("<Destroy>", self.on_destroy)

        # Configure the hierarchy window
        self.title(name)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 840
        window_height = 880
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
        self.project_combo.bind("<<ComboboxSelected>>", lambda event: self.add_or_remove_project())
        #self.project_listbox = tk.Listbox(self.form_frame, selectmode=tk.MULTIPLE, height=1)
        if isinstance(parent,HierarchyWindow):
            value = parent.project_combo.get()
            if value not in self.main_app.project_options:
                main_app.add_project_option(value)
                self.project_combo = ttk.Combobox(self.form_frame, values=self.main_app.project_options)
            self.project_combo.set(value)
        #self.project_combo.set("VISize")
        #self.populate_project_listbox()
        self.project_combo.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="W")

        self.projects_var = tk.StringVar()
        self.projects_label = ttk.Label(self.form_frame, font=("Arial", 10), textvariable=self.projects_var, background="white")
        self.projects_label.grid(row=1, column=1, columnspan=8, padx=9, pady=10, sticky="W")
        self.projects_var.set("; ".join(self.projects))

        # Add papertrail label and entry
        self.papertrail_label = ttk.Label(self.form_frame, text="Papertrail:")
        self.papertrail_label.grid(row=1, column=3, padx= 5, pady=0, sticky="E")
        self.papertrail_var = tk.StringVar()
        if isinstance(parent,HierarchyWindow):
            self.papertrail_var = tk.StringVar(value=parent.key_entry.get())
        self.papertrail_entry = ttk.Entry(self.form_frame, textvariable=self.papertrail_var, width=23)
        self.papertrail_entry.grid(row=1, column=4, columnspan=3, padx=0, pady=5, sticky="W")

    # Add a horizontal separator
        self.separator = ttk.Separator(self.form_frame, orient="horizontal")
        self.separator.grid(row=3, column=0, columnspan=10, pady=5, sticky="ew")

        # Add label and entry for key
        self.key_label = ttk.Label(self.form_frame, text="Key:")
        self.key_label.grid(row=5, column=0, columnspan=1, padx=5, pady=5, sticky="E")
        self.key_var = tk.StringVar()
        self.key_entry = ttk.Entry(self.form_frame, textvariable=self.key_var, width=23)
        self.key_entry.grid(row=5, column=1, columnspan=3, padx=5, pady=5, sticky="W")
        self.key_entry.bind("<KeyRelease>", lambda event: self.update_tree())

        self.validate_key_btn = ttk.Button(self.form_frame, text="Validate", command=self.validate_key, width=7)
        self.validate_key_btn.grid(row=5, column=5, padx=5, pady=5, sticky="W")
        self.key_validation = tk.StringVar()
        self.key_validation_label = ttk.Label(self.form_frame, font=("Lucida Console", 8), textvariable=self.key_validation)
        self.key_validation_label.grid(row=5, column=3, padx=5, pady=0, sticky="W")

        self.copy_key_btn = ttk.Button(self.form_frame, text="Copy", command=self.copy_key)
        self.copy_key_btn.grid(row=5, column=6, padx=5, pady=0, sticky="W")

        self.copy_keycite_btn = ttk.Button(self.form_frame, text="\\cite", command=self.copy_keycite)
        self.copy_keycite_btn.grid(row=5, column=7, padx=5, pady=0, sticky="W")

        # add bibtex label and entry
        self.bibtex_label = ttk.Label(self.form_frame, text="Bibtex:")
        self.bibtex_label.grid(row=20, column=0, columnspan=1, padx=5, pady=5, sticky="E")
        self.bibtex_field = tk.Text(self.form_frame, width=50, height=12, wrap="word")
        #self.bibtex_field.pack(pady=5, fill=tk.BOTH, padx=10, expand=True)
        self.bibtex_field.grid(row=20, column=1, columnspan=4, rowspan=7, padx=5, pady=5, sticky="W")
        self.bibtex_chars = tk.StringVar(value="0/2000")
        self.bibtex_chars_label = ttk.Label(self.form_frame, font=("Lucida Console", 5), textvariable=self.bibtex_chars)
        self.bibtex_chars_label.grid(row=24, column=1, padx=8, pady=8, sticky="SW")
        self.bibtex_field.bind("<KeyRelease>", lambda event: [self.update_bibtex_chars(), self.update_abstract_chars(), self.update_notes_chars(), self.parse_bibtex(), self.update_tree()])

        self.second_bibtex_label = ttk.Label(self.form_frame, text="Bibtex cmds:")
        self.second_bibtex_label.grid(row=20, column=5, padx=5, pady=5, sticky="N")

        self.parse_bibtex_btn = ttk.Button(self.form_frame, text="Parse", command=self.parse_bibtex, width=5)
        self.parse_bibtex_btn.grid(row=20, column=6, padx=5, pady=0, sticky="N")

        self.copy_bibtex_btn = ttk.Button(self.form_frame, text="Copy", command=self.copy_bibtex, width=5)
        self.copy_bibtex_btn.grid(row=20, column=7, padx=5, pady=0, sticky="N")

        self.bibtex_radio_options = tk.StringVar(value="original")
        self.bibtex_radio_btn1 = tk.Radiobutton(self.form_frame, text="original", variable=self.bibtex_radio_options, value="original", command=self.format_bibtex)
        self.bibtex_radio_btn2 = tk.Radiobutton(self.form_frame, text="reformatted", variable=self.bibtex_radio_options, value="reformatted", command=self.format_bibtex)
        self.bibtex_radio_btn3 = tk.Radiobutton(self.form_frame, text="reduced", variable=self.bibtex_radio_options, value="reduced", command=self.format_bibtex)

        self.bibtex_radio_btn1.grid(row=21, column=5, padx=5, pady=5, sticky="w")
        self.bibtex_radio_btn2.grid(row=21, column=6, padx=5, pady=5, sticky="w")
        self.bibtex_radio_btn3.grid(row=21, column=7, padx=5, pady=5, sticky="w")

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

        self.citation_style_options = self.main_app.journal_style_options
        self.citation_style1_combo = ttk.Combobox(self.form_frame, values=self.citation_style_options, width=7)
        self.citation_style1_combo.grid(row=23, column=5, pady=5, padx=(30,5), sticky="W")
        self.citation_style1_combo.set("--style--")
        self.citation_style2_combo = ttk.Combobox(self.form_frame, values=self.citation_style_options, width=7)
        self.citation_style2_combo.grid(row=24, column=5, pady=5, padx=(30,5), sticky="W")
        self.citation_style2_combo.set("--style--")


        self.journal_styling_options = ["--format--","Plain","HTML", "LaTeX", "RichText"]
        self.journal_styling1_combo = ttk.Combobox(self.form_frame, values=self.journal_styling_options, width=7)
        self.journal_styling1_combo.grid(row=23, column=6, pady=5, padx=5, sticky="W")
        self.journal_styling1_combo.set("--format--")
        self.journal_styling2_combo = ttk.Combobox(self.form_frame, values=self.journal_styling_options, width=7)
        self.journal_styling2_combo.grid(row=24, column=6, pady=5, padx=5, sticky="W")
        self.journal_styling2_combo.set("--format--")

        self.referencing_options = ["--refs--","\\cite","doi", "doi+cite","None"]
        self.referencing1_combo = ttk.Combobox(self.form_frame, values=self.referencing_options, width=7)
        self.referencing1_combo.grid(row=23, column=7, pady=5, padx=5, sticky="W")
        self.referencing1_combo.set("--refs--")
        self.referencing2_combo = ttk.Combobox(self.form_frame, values=self.referencing_options, width=7)
        self.referencing2_combo.grid(row=24, column=7, pady=5, padx=5, sticky="W")
        self.referencing2_combo.set("--refs--")

        # Add year label and entry
        self.year_label = ttk.Label(self.form_frame, text="Year:")
        self.year_label.grid(row=27, column=2, padx=5, pady=5, sticky="E")
        self.year_var = tk.StringVar()
        self.year_entry = ttk.Entry(self.form_frame, textvariable=self.year_var, width=10)
        self.year_entry.grid(row=27, column=3, padx=5, pady=5, sticky="W")

        # Add citation count label and entry
        self.count_label = ttk.Label(self.form_frame, text="Cite-Count:")
        self.count_label.grid(row=27, column=0, padx=5, pady=5, sticky="E")
        validate_number = self.register(self.only_numbers)
        self.count_var = tk.StringVar()
        self.count_entry = ttk.Entry(self.form_frame, textvariable=self.count_var, validate="key", validatecommand=(validate_number, "%S"), width=10)
        self.count_entry.grid(row=27, column=1, padx=5, pady=5, sticky="W")

        # add title label and entry
        self.title_label = ttk.Label(self.form_frame, text="Title:")
        self.title_label.grid(row=30, column=0, padx=5, pady=5, sticky="E")
        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(self.form_frame, textvariable=self.title_var, width=38)
        self.title_entry.grid(row=30, column=1, columnspan=3, padx=5, pady=5, sticky="W")

        self.copy_title_btn = ttk.Button(self.form_frame, text="Copy", command=self.copy_title)
        self.copy_title_btn.grid(row=30, column=5, padx=5, pady=0, sticky="W")

        self.cite_title_btn = ttk.Button(self.form_frame, text="\\cite", command=self.cite_title)
        self.cite_title_btn.grid(row=30, column=6, padx=5, pady=0, sticky="W")

        self.fullcite_title_btn = ttk.Button(self.form_frame, text="\\keycite", command=self.fullcite_title)
        self.fullcite_title_btn.grid(row=30, column=7, padx=5, pady=0, sticky="W")

        self.short_title_label = ttk.Label(self.form_frame, text="Short title:")
        self.short_title_label.grid(row=31, column=0, padx=5, pady=5, sticky="E")
        self.short_title_var = tk.StringVar()
        self.short_title_entry = tk.Entry(self.form_frame, textvariable=self.short_title_var, width=25)
        self.short_title_entry.grid(row=31, column=1, columnspan=2, padx=5, pady=5, sticky="W")

        self.short_title_length_var = tk.StringVar()
        self.short_title_length_options = list(map(str, list(range(1,9))))
        self.short_title_length_combo = ttk.Combobox(self.form_frame, values=self.short_title_length_options, width=3)
        self.short_title_length_combo.grid(row=31, column=3, padx=5, pady=5, sticky="E")

        self.copy_short_title_btn = ttk.Button(self.form_frame, text="Copy", command=lambda: self.main_app.copy_to_clipboard(self.short_title_var.get()))
        self.copy_short_title_btn.grid(row=31, column=5, padx=5, pady=5, sticky="W")

        #small_default_font = tkFont.nametofont("TkDefaultFont")
        #small_default_font.configure(size=8)  # Change default size

        self.authors_label = ttk.Label(self.form_frame, text="Authors:", font=("Lucida Grande", 9))
        self.authors_label.grid(row=33, column=0, padx=5, pady=5, sticky="E")
        self.authors_var = tk.StringVar()
        self.authors_entry = tk.Entry(self.form_frame, textvariable=self.authors_var, width=57, font=("Lucida Grande", 7))
        self.authors_entry.grid(row=33, column=1, columnspan=3, padx=5, pady=5, ipady=1, sticky="W")
        self.authors_entry.bind("<KeyRelease>", lambda event: self.parse_authors_entry())

        self.action_options = ["-action-","copy","cite-#1", "cite-#2", "cite-global"]
        self.authors_action_combo = ttk.Combobox(self.form_frame, values=self.action_options, width=7, state="readonly")
        self.authors_action_combo.title = "authors_action"
        self.authors_action_combo.grid(row=33, column=6, padx=5, pady=5, sticky="W")
        self.authors_action_combo.set(self.authors_action_combo["values"][0])
        self.authors_action_combo.bind("<<ComboboxSelected>>", self.how_to_copy)

        self.authors_1_button = tk.Button(self.form_frame, text="#1", width=1, command=self.get_citation)
        self.authors_1_button.configure(relief="flat")
        self.authors_1_button.grid(row=33, column=7, padx=0, pady=(5,10), ipadx=0, ipady=0, sticky="W")

        # add abstract label and textfield
        self.abstract_label = ttk.Label(self.form_frame, text="Abstract:")
        self.abstract_label.grid(row=40, column=0, padx=5, pady=5, sticky="E")
        self.abstract_field = tk.Text(self.form_frame, width=50, height=5, wrap="word")
        self.abstract_field.grid(row=40, column=1, columnspan=4, padx=5, pady=5, sticky="W")
        self.abstract_chars = tk.StringVar(value="0/2000")
        self.abstract_chars_label = ttk.Label(self.form_frame, font=("Lucida Console", 5), textvariable=self.abstract_chars)
        self.abstract_chars_label.grid(row=40, column=1, padx=8, pady=8, sticky="SW")
        self.abstract_field.bind("<KeyRelease>", lambda event: [self.update_abstract_chars()])

        # add journal label and entry
        self.journal_label = ttk.Label(self.form_frame, text="Journal:")
        self.journal_label.grid(row=50, column=0, padx=5, pady=5, sticky="E")
        self.journal_var = tk.StringVar()
        self.journal_entry = tk.Entry(self.form_frame, textvariable=self.journal_var, width=38)
        self.journal_entry.grid(row=50, column=1, columnspan=3, padx=5, pady=5, sticky="W")

        # Add pub type label and options
        self.type_label = ttk.Label(self.form_frame, text="Pub-Type:")
        self.type_label.grid(row=55, column=2, padx=5, pady=5, sticky="E")
        self.type_combo = ttk.Combobox(self.form_frame, values=self.main_app.type_options, width=7)
        self.type_combo.set(self.main_app.type_options[0])
        self.type_combo.grid(row=55, column=3, padx=5, pady=5, sticky="W")

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
        self.notes_chars_label.grid(row=80, column=1, padx=8, pady=8, sticky="SW")
        self.notes_field.bind("<KeyRelease>", lambda event: [self.update_notes_chars()])

        send_button_style = ttk.Style()
        send_button_style.configure("Custom.TButton", background="white", bordercolor="red", borderwidth=2)

        self.send_button = ttk.Button(self.form_frame, text="Send to Notion", command=self.send_data_to_notion, style="Custom.TButton",  width=15)
        self.send_button.grid(row=80, column=6, columnspan=2, padx=5, pady=5, sticky="SW")

        # Add a horizontal separator
        self.separator_pdf = ttk.Separator(self.form_frame, orient="horizontal")
        self.separator_pdf.grid(row=89, column=0, columnspan=10, pady=10, sticky="ew")

        # Add a label and entry for "PDF"
        self.pdf_label = ttk.Label(self.form_frame, text="PDF:")
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

        self.bind_all("<KeyPress-Alt_L>", lambda event: self.switch_to_load())  # Windows/Linux Alt Key
        self.bind_all("<KeyRelease-Alt_L>", lambda event:  self.switch_to_validate())
        #self.bind("<KeyRelease-Alt_L>", lambda event: self.switch_to_validate)

        # # If you want Command (⌘) key on macOS:
        # self.bind("<KeyPress-Command_L>", lambda event: self.switch_to_load)
        # self.bind("<KeyRelease-Command_L>", lambda event: self.switch_to_validate)
        #
        # self.bind("<Command_L>", lambda event: self.switch_to_load)
        # self.bind("<KeyRelease-Meta_L>", lambda event: self.switch_to_validate)
        #
        #self.bind("<KeyPress>", lambda event: print(f"Pressed: {event.keysym}"))

        self.inherit_from_parents()
        # Add this window to the main app's window reference
        self.main_app.windows[self.name] = self
        #pprint.pprint(f"Parent: {type(parent)}")

    def get_citation(self):
        print(self.cm.process_citation({"style":"IEEE"}))
        #print("NOT IMPLEMENTED YET")

    def inherit_projects(self):
        if isinstance(self.parent,HierarchyWindow):
            self.projects = self.parent.projects.copy()
        else:
            self.projects = []

    def inherit_from_parents(self):
        if isinstance(self.parent,HierarchyWindow):
            self.citation_style1_combo.set(self.parent.citation_style1_combo.get())
            self.citation_style2_combo.set(self.parent.citation_style2_combo.get())
            self.journal_styling1_combo.set(self.parent.journal_styling1_combo.get())
            self.journal_styling2_combo.set(self.parent.journal_styling2_combo.get())
            self.referencing1_combo.set(self.parent.referencing1_combo.get())
            self.referencing2_combo.set(self.parent.referencing2_combo.get())
        else:
            favs = self.main_app.favorite_citation_settings
            self.citation_style1_combo.set(favs.get("style1", self.citation_style1_combo["values"][0]))
            self.citation_style2_combo.set(favs.get("style2", self.citation_style2_combo["values"][0]))
            self.journal_styling1_combo.set(favs.get("italics1", self.journal_styling1_combo["values"][0]))
            self.journal_styling2_combo.set(favs.get("italics2", self.journal_styling2_combo["values"][0]))
            self.referencing1_combo.set(favs.get("refs1", self.referencing1_combo["values"][0]))
            self.referencing2_combo.set(favs.get("refs2", self.referencing2_combo["values"][0]))



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
        self.validate_key_btn.config(text="Load", command=self.load_key, width=8)
        self.send_button.config(text="Update in Notion", command=self.update_notion_entry, width=15)

    def switch_to_validate(self):
        """Switch button back to 'Validate' mode when modifier key is released"""
        self.validate_key_btn.config(text="Validate", command=self.validate_key, width=8)
        self.send_button.config(text="Send to Notion", command=self.send_data_to_notion,  width=15)

    def update_bibtex_chars(self):
        count = len(self.bibtex_field.get("1.0", tk.END))
        self.bibtex_chars.set(f"{count}/2000")

    def update_abstract_chars(self):
        count = len(self.abstract_field.get("1.0", tk.END))
        self.abstract_chars.set(f"{count}/2000")

    def update_notes_chars(self):
        count = len(self.notes_field.get("1.0", tk.END))
        self.notes_chars.set(f"{count}/2000")

    def copy_keycite(self):
        value = self.key_var.get()
        self.main_app.copy_to_clipboard("\\cite{"+value+"}")

    def copy_key(self):
        value = self.key_var.get()
        self.main_app.copy_to_clipboard(value)


    def copy_bibtex(self):
            value = self.bibtex_field.get("1.0", tk.END).strip()
            self.main_app.copy_to_clipboard(value)

    def cite_mla(self, style="plain"):
        self.main_app.copy_to_clipboard(self.cm.reference_mla_style(style))

    def cite_ieee(self, style="plain"):
        self.main_app.copy_to_clipboard(self.cm.reference_ieee_style(style))

    def copy_title(self):
        value = self.title_var.get()
        self.main_app.copy_to_clipboard(value)

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
        self.parsed_bibtex += 1
        bibtex = self.bibtex_field.get("1.0", tk.END)
        self.cm.set_citation_key(self.key_var.get())
        self.cm.parse_bibtex(bibtex)
        self.key_var.set(self.cm.get_citation_key())
        bib_data = bibtexparser.loads(bibtex)
        for entry in bib_data.entries:
            pprint.pprint(f"Entry: {entry}")
            self.year_var.set(entry["year"]) if "year" in entry else None
            if entry['ID'] and self.key_entry.get():
                entry['ID'] = self.key_entry.get()
            if "eprint" in entry:
                del entry["eprint"]
            if "abstract" in entry:
                self.abstract_field.insert("1.0", entry["abstract"])
                del entry["abstract"]
            if "url" in entry:
                self.bibtex_url = entry["url"].strip()
            if "author" in entry:
                self.bibtex_authors = entry["author"]
                #self.parse_bibtex_authors()
            if "doi" in entry:
                self.bibtex_doi = entry["doi"].strip()
            if "title" in entry:
                self.title_var.set(entry["title"])
            if "journal" in entry:
                self.journal_var.set(entry["journal"])
            elif "booktitle" in entry:
                self.journal_var.set(entry["booktitle"])


        self.set_link_doi()
        self.match_venue()
        self.authors_var.set(self.cm.authors.get_string(" and ")) #type: ignore
        #self.bibtex_field.delete("1.0", tk.END)
        #self.bibtex_field.insert("1.0", bibtexparser.dumps(bib_data))
        self.format_bibtex()
        self.update_cm()

    def format_bibtex(self):
        cmd = self.bibtex_radio_options.get()
        print(cmd)
        f = self.cm.bibtex_formatter
        m = getattr(f, cmd, None)
        if m:
            self.bibtex_field.delete("1.0",tk.END)
            self.bibtex_field.insert("1.0", m())
        else:
            raise ValueError(f"Invalid method: {m}")


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
                return  # Stop after the first match

        # If no match is found, clear or set a default
        self.venue_combo.set("")

    def validate_key(self):
        self.start_waiting_anim()
        self.update_key_validation()

    def start_waiting_anim(self):
        self.is_waiting = True
        self.waiting_for_response_anim()

    def update_bibtex_key(self):
        bibtex = self.bibtex_field.get("1.0", tk.END)
        bib_data = bibtexparser.loads(bibtex)
        for entry in bib_data.entries:
            if entry['ID']:
                entry['ID'] = self.key_entry.get()

        self.bibtex_field.delete("1.0", tk.END)
        self.bibtex_field.insert("1.0", bibtexparser.dumps(bib_data))

    def how_to_copy(self, event):
        widget = event.widget
        selected_value = widget.get()
        widget.set(selected_value)
        print(f"Combobox: {widget.title}, Selected: {selected_value}")
        self.main_app.after(1000, lambda: widget.set(widget["values"][0]))
        #widget.set("")
        self.focus_set()
        #widget.set(widget["values"][0])
        #self.focus_set()

    def update_key_validation(self):
        self.is_waiting = True
        #self.key_validation.set("waiting for response")
        #self.key_validation_label.config(text="Waiting for response", foreground="black")
        #self.waiting_for_response_anim()
        if self.check_key():
            self.is_waiting = False
            self.key_validation.set("is available")
            self.key_validation_label.config(foreground="green")
            self.update_bibtex_key()
        else:
            self.is_waiting = False
            self.key_validation.set("is NOT available!!")
            self.key_validation_label.config(foreground="red")

    def waiting_for_response_anim(self): #not working
        """Animate the label by adding dots."""
        self.dots
        if self.is_waiting:
            # Update the text with the current number of dots
            self.dots = (self.dots + 1) % 4
            self.key_validation.set("Waiting for response" + "." * self.dots)
            self.key_validation_label.config(foreground="black")

            # Schedule the next animation frame
            self.after(500, self.waiting_for_response_anim)

    def check_key(self):
        title = self.key_entry.get()
        return self.main_app.notion_api.validate_key_availability(title)

    def load_key(self):
        title = self.key_entry.get()
        page = self.main_app.notion_api.request_page(title)
        pprint.pprint(page)
        self.clear_projects()
        for project in page.project:
            self.add_or_remove_project(project)
        self.notion_page_id = page.notion_page_id
        self.bibtex_field.insert("1.0", page.bibtex_safe())
        self.title_var.set(page.title_safe())
        self.authors = page.authors.get_string(", ")
        self.authors_var.set(self.authors)
        self.abstract_field.insert("1.0", page.abstract_safe())
        self.journal_var.set(page.journal_safe())
        self.venue_combo.set(page.venue_safe())
        self.year_var.set(page.year_safe())
        self.count_var.set(page.count_safe())
        self.pdf_var.set(self.pdf_handler.find_paper_path(title))
        #pprint.pprint(dir(page))
        #print(page.bibtex)


        self.loaded_from_notion = True


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


    def send_data_to_notion(self):
        if self.sent_to_notion:
            messagebox.showerror("Error", "You already sent this - please switch to update!")
            return
        if self.loaded_from_notion:
            messagebox.showerror("Error", "Entry was loaded from Notion - please switch to update!")
            return
        try:
            data = self.prepare_data_for_notion()
            self.main_app.notion_api.create_page(data)
            self.sent_to_notion = True
        except ValueError as e:
            messagebox.showwarning("ValueError", str(e))

    def update_notion_entry(self):
        if not (self.sent_to_notion or self.loaded_from_notion):
            messagebox.showerror("Error", "This is probably not gonna work")
        try:
            data = self.prepare_data_for_notion()
            data["notion_page_id"] = self.notion_page_id
            self.main_app.notion_api.update_page(data)
        except ValueError as e:
            messagebox.showwarning("ValueError", str(e))

    def get_bibtex_field(self):
        return self.bibtex_field.get("1.0", tk.END).strip()

    def get_abstract_field(self):
        return self.abstract_field.get("1.0", tk.END).strip()

    def get_notes_field(self):
        return self.notes_field.get("1.0", tk.END).strip()

    def get_text_field(self, field):
        return field.get("1.0", tk.END).strip()

    # TODO: prepare_data_for_notion -> integrate in CitationManager
    def prepare_data_for_notion(self):
        data = {}
        data["key"] = self.key_entry.get()
        data["bibtex"] = self.bibtex_field.get("1.0", tk.END).strip()
        data["papertrail"] = self.papertrail_entry.get()
        data["title"] = self.title_entry.get()
        data["year"] = int(self.year_entry.get())
        data["project"] = self.projects
        data["abstract"] = self.abstract_field.get("1.0", tk.END).strip()
        data["count"] = self.count_var.get()
        data["type"] = self.type_combo.get()
        data["notes"] = self.notes_field.get("1.0", tk.END).strip()
        data["link_doi"] = self.link_doi_entry.get().strip()
        data["journal"] = self.journal_var.get()
        data["venue"] = self.venue_combo.get()
        data["authors"] = self.cm.authors.get_array()
        return data

    # NOTE: update_cm -> can it be used for prepare_data_for_notion?
    def update_cm(self):
        cm = self.cm
        cm.citation_key = self.key_entry.get()
        cm.modified_bibtex_file = self.get_text_field(self.bibtex_field)
        cm.papertrail = self.papertrail_entry.get()
        cm.title = self.title_entry.get()
        cm.year = int(self.year_entry.get())
        cm.projects = self.projects
        cm.abstract = self.get_text_field(self.abstract_field)
        cm.count = self.count_var.get()
        cm.type = self.type_combo.get()
        cm.notes = self.get_text_field(self.notes_field)
        cm.link_doi = self.link_doi_entry.get().strip()
        cm.journal = self.journal_var.get()
        cm.venue = self.venue_combo.get() if self.venue_combo.get() else cm.venue
        cm.authors =
        self.cm = cm
        pprint.pprint(self.cm)


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
        key_content = self.key_entry.get().strip()
        try:
            new_path = self.pdf_handler.rename_and_move_pdf(key_content)
            self.pdf_var.set(new_path)
        except (ValueError, FileNotFoundError, FileExistsError) as e:
            messagebox.showerror("Error", str(e))

    def open_pdf(self):
        print("NEW METHOD IS CALLED FOR OPENING")
        """Handle UI interaction for opening the PDF."""
        try:
            self.pdf_handler.open_pdf()
        except (FileNotFoundError, OSError) as e:
            messagebox.showerror("Error", str(e))

    def clear_fields(self):
        self.sent_to_notion = False
        self.loaded_from_notion = False

        self.key_entry.delete(0, tk.END)
        self.title_var.set("")
        self.title_entry.delete(0, tk.END)
        self.year_var.set("")
        self.year_entry.delete(0, tk.END)
        self.bibtex_field.delete("1.0", tk.END)
        self.abstract_field.delete("1.0", tk.END)
        self.pdf_var.set("")
        self.pdf_entry.delete(0, tk.END)
        self.notes_field.delete("1.0", tk.END)
        self.count_var.set("")
        self.count_entry.delete(0, tk.END)
        self.authors_var.set("")
        self.link_doi_var.set("")
        self.link_doi_entry.delete(0, tk.END)
        self.sent_flag = False
        self.venue_combo.set("")
        self.journal_var.set("")
        #print(f"sent_flag: {sent_flag}")

    def confirm_with_ok_cancel(self):
        response = messagebox.askokcancel("Confirmation", "Are you sure? You haven't sent it yet...")
        if response:  # User clicked 'OK'
            clear_fields()
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
    app = MainApp()
    app.mainloop()
