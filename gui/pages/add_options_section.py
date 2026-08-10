import tkinter as tk
from tkinter import ttk


class AddOptionsSection(ttk.LabelFrame):
    """Section for adding new values to the dropdown option lists."""

    def __init__(self, parent, category_options, refresh_callback=None):
        super().__init__(parent, text="Add options", padding=12)
        self.category_options = category_options
        self.refresh_callback = refresh_callback
        self.option_entries = {}

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Type a new value for each category and save it to update the dropdown lists.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", anchor="w")

        for category_name in ["Sensor type", "AC/DC", "Substrate", "Graphene", "Coating"]:
            row_frame = ttk.Frame(input_frame)
            row_frame.pack(fill="x", pady=2, anchor="w")

            ttk.Label(row_frame, text=category_name, width=16, anchor="w").pack(side="left")
            entry = ttk.Entry(row_frame, width=24)
            entry.pack(side="left", padx=(8, 0))
            self.option_entries[category_name] = entry

        save_button = ttk.Button(self, text="Save choices", command=self._save_added_options)
        save_button.pack(anchor="e", pady=(8, 0))

    def _save_added_options(self):
        for category_name, entry in self.option_entries.items():
            new_value = entry.get().strip()
            if not new_value:
                continue

            options = self.category_options.setdefault(category_name, [])
            if new_value not in options:
                options.append(new_value)

            entry.delete(0, tk.END)

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        pass
