import tkinter as tk
import platform
from tkinter import filedialog, messagebox, ttk
import json
import os
from config_handler import ConfigHandler

class ConfigEditor(tk.Toplevel):
    """A subwindow for editing JSON configuration."""
    def __init__(self, parent, initial_config="config.json"):
        super().__init__(parent)
        self.title("Config Editor")
        self.geometry("1000x1000+20+100")

        self.config_dir = "configs"
        self.config_path = os.path.join(self.config_dir, initial_config)
        self.last_saved_state = ""

        # Stack for Undo (Stores last 20 changes)
        self.undo_stack = []
        self.max_undo = 20

        # Dropdown for selecting configuration
        button_frame = tk.Frame(self)
        button_frame.pack(fill="x", padx=10, pady=5)

        self.config_var = tk.StringVar(value=initial_config)
        self.config_dropdown = ttk.Combobox(button_frame, textvariable=self.config_var, state="readonly")
        self.config_dropdown.pack(side="left", padx=5)
        self.update_config_list()
        self.config_dropdown.bind("<<ComboboxSelected>>", self.change_config)

        # Buttons
        tk.Button(button_frame, text="Save", command=self.save_json).pack(side="left", padx=5)
        tk.Button(button_frame, text="Undo (Z)", command=self.undo).pack(side="left", padx=5)
        tk.Button(button_frame, text="Close", command=self.destroy).pack(side="right", padx=5)

        # Text area for JSON editing
        self.text_area = tk.Text(self, wrap="word", font=("Courier", 12), undo=True)
        self.text_area.pack(expand=True, fill="both", padx=10, pady=10)

        # Bind keyboard shortcuts
        is_mac = platform.system() == "Darwin"
        cmd_key = "Command" if is_mac else "Control"
        self.text_area.bind_class("Text", f"<{cmd_key}-z>", self.undo)
        self.text_area.bind("<KeyRelease>", self.store_undo)
        self.bind(f"<{cmd_key}-s>", lambda event: self.save_json())
        self.bind_all(f"<{cmd_key}-q>", lambda event: self.destroy())

        # Load initial config
        self.load_json()

    def update_config_list(self):
        """Update the dropdown with available config files."""
        configs = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        self.config_dropdown['values'] = configs

    def change_config(self, event=None):
        """Change the loaded configuration with a check for unsaved changes."""
        if self.has_unsaved_changes():
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                "The current file has been modified. Do you want to save the changes before switching?"
            )
            if response:  # Yes
                self.save_json()
            elif response is None:  # Cancel
                self.config_var.set(os.path.basename(self.config_path))
                return  # Do not switch

        selected_config = self.config_var.get()
        self.config_path = os.path.join(self.config_dir, selected_config)
        self.load_json()

    def has_unsaved_changes(self):
        """Check if the current content has unsaved changes."""
        current_state = self.text_area.get("1.0", tk.END).strip()
        return current_state != self.last_saved_state

    def store_undo(self, event=None):
        """Store the current state in the undo stack."""
        if len(self.undo_stack) >= self.max_undo:
            self.undo_stack.pop(0)
        self.undo_stack.append(self.text_area.get("1.0", tk.END).strip())

    def undo(self, event=None):
        """Revert to the last stored state when 'Z' is pressed."""
        if self.undo_stack:
            last_state = self.undo_stack.pop()
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, last_state)
        else:
            messagebox.showinfo("Undo", "No more actions to undo!")

    def load_json(self):
        """Load and display the JSON config file."""
        json_data = ConfigHandler.load_config(self.config_path)
        if json_data:
            formatted_json = json.dumps(json_data, indent=4)
            self.text_area.delete("1.0", tk.END)
            self.text_area.insert(tk.END, formatted_json)
            self.last_saved_state = formatted_json.strip()
            self.store_undo()
        else:
            self.text_area.delete("1.0", tk.END)

    def save_json(self):
        """Save the JSON content from the editor back to the config file."""
        try:
            json_data = self.text_area.get("1.0", tk.END).strip()
            parsed_json = json.loads(json_data)

            with open(self.config_path, "w", encoding="utf-8") as file:
                json.dump(parsed_json, file, indent=4)

            self.last_saved_state = json_data  # Update last saved state
            messagebox.showinfo("Success", f"Config file '{os.path.basename(self.config_path)}' saved successfully!")
        except json.JSONDecodeError:
            messagebox.showerror("Error", "Invalid JSON format!")

# Uncomment below for standalone testing
# if __name__ == "__main__":
#     root = tk.Tk()
#     root.withdraw()  # Hide main window
#     editor = ConfigEditor(root)
#     root.mainloop()
