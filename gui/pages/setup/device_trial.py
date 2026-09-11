"""Device page section for capturing labelled trial snapshots and managing shape options."""

import tkinter as tk
from tkinter import ttk

from backend.resistance_snapshot_backend import TrialSnapshotBackend
from backend.shape_classifier_backend import ShapeClassifierBackend
from backend.shape_options_backend import ShapeOptionsData
from gui.controls.dropdown_object import DropdownObject


class AddTrialSnapshotSection(ttk.LabelFrame):
    """Section that captures a steady-state resistance snapshot for one trial."""

    def __init__(self, parent, shape_data: ShapeOptionsData, refresh_callback=None, device_getter=None):
        super().__init__(parent, text="Add trial data snapshot", padding=12)
        self.shape_data = shape_data
        self.refresh_callback = refresh_callback
        # device_getter is supplied by the Device page so this section can read the
        # live device without importing the page itself.
        self.device_getter = device_getter
        self.snapshot_backend = TrialSnapshotBackend()

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Select the shape being pressed, apply the steady load, then capture one snapshot of every sensing point's relative resistance.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        snapshot_button_frame = ttk.Frame(self)
        snapshot_button_frame.pack(fill="x", pady=(0, 8))
        snapshot_button = ttk.Button(snapshot_button_frame, text="Take snapshot", command=self._take_snapshot)
        snapshot_button.pack(side="left")

        self.shape_dropdown = DropdownObject(
            self,
            "Shape",
            self._get_shape_options(),
            default_value="No selection",
            width=18,
        )
        self.shape_dropdown.pack(anchor="w")

        # Persistent red warning label, matching the message_label pattern used by
        # the config/design/options sections. It stays visible until the next attempt.
        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

    def _take_snapshot(self):
        """Validate inputs, read the latest channel values, and append one trial row."""
        selected_shape = self.shape_dropdown.get()
        if not selected_shape or selected_shape == "No selection":
            self.message_label.config(text="Please select a shape before taking a snapshot.")
            return

        device = self.device_getter() if self.device_getter is not None else None
        if device is None or not device.is_open or not device.running:
            self.message_label.config(text="Cannot take a snapshot: the device is not connected and running.")
            return

        relative_resistances = self.snapshot_backend.get_latest_relative_resistances(device)
        if relative_resistances is None:
            self.message_label.config(text="Need a complete 12-channel reading and a locked baseline before saving.")
            return

        try:
            trial_id = self.snapshot_backend.save_snapshot(relative_resistances, selected_shape)
        except Exception:
            self.message_label.config(text="Snapshot could not be saved to trial_data.csv.")
            return

        # Success: clear the warning, as the other sections do after a valid save.
        self.message_label.config(text=f"Snapshot saved as trial {trial_id}.")

        # Keep the remove dropdown aligned with the CSV after a new trial is saved.
        if self.refresh_callback is not None:
            self.refresh_callback()

    def _get_shape_options(self):
        return ["No selection"] + self.shape_data.get_shapes()

    def get_selected_shape(self):
        """Return the shape label the next snapshot should be recorded against."""
        return self.shape_dropdown.get()

    def refresh(self):
        # Keep the dropdown in sync when shapes are added or removed elsewhere in this section.
        current_value = self.shape_dropdown.get()
        available_options = self._get_shape_options()
        self.shape_dropdown.dropdown.configure(values=available_options)
        if current_value not in available_options:
            self.shape_dropdown.set("No selection")


class RemoveTrialSnapshotSection(ttk.LabelFrame):
    """Section for removing a saved trial row from trial_data.csv."""

    def __init__(self, parent, refresh_callback=None):
        super().__init__(parent, text="Remove trial data snapshot", padding=12)
        self.refresh_callback = refresh_callback
        self.snapshot_backend = TrialSnapshotBackend()

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose a saved trial and remove that snapshot from the CSV.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        self.trial_dropdown = DropdownObject(
            self,
            "Trial",
            self._get_trial_options(),
            default_value="No selection",
            width=22,
        )
        self.trial_dropdown.pack(anchor="w")

        self.message_label = ttk.Label(self, text="", foreground="red", wraplength=1000, justify="left")
        self.message_label.pack(anchor="w", pady=(8, 0))

        remove_button = ttk.Button(self, text="Remove trial", command=self._remove_selected_trial)
        remove_button.pack(anchor="e", pady=(8, 0))

    def _get_trial_options(self):
        return ["No selection"] + self.snapshot_backend.get_trial_display_options()

    def _parse_selected_trial_id(self):
        selected_value = self.trial_dropdown.get()
        if not selected_value or selected_value == "No selection":
            return None

        # Dropdown labels are formatted as 'Trial 3' or 'Trial 3 (circle)'.
        parts = selected_value.split()
        if len(parts) < 2:
            return None

        try:
            return int(parts[1])
        except ValueError:
            return None

    def _remove_selected_trial(self):
        trial_id = self._parse_selected_trial_id()
        if trial_id is None:
            self.message_label.config(text="Please choose a trial to remove.")
            return

        removed = self.snapshot_backend.remove_trial(trial_id)
        if not removed:
            self.message_label.config(text="That trial could not be removed from trial_data.csv.")
            return

        self.message_label.config(text=f"Trial {trial_id} removed.")

        # Refresh sibling sections so the new state is visible immediately.
        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.trial_dropdown.dropdown.configure(values=self._get_trial_options())
        self.trial_dropdown.set("No selection")
        self.message_label.config(text="")


class AddShapeOptionSection(ttk.LabelFrame):
    """Section for adding new shapes to the trial shape option list."""

    def __init__(self, parent, shape_data: ShapeOptionsData, refresh_callback=None):
        super().__init__(parent, text="Add shape option", padding=12)
        self.shape_data = shape_data
        self.refresh_callback = refresh_callback

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Type a new shape name and save it to update the shape option list.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        input_frame = ttk.Frame(self)
        input_frame.pack(fill="x", anchor="w")

        ttk.Label(input_frame, text="Shape", width=16, anchor="w").pack(side="left")
        self.shape_entry = ttk.Entry(input_frame, width=24)
        self.shape_entry.pack(side="left", padx=(8, 0))

        save_button = ttk.Button(self, text="Save choices", command=self._save_added_shape)
        save_button.pack(anchor="e", pady=(8, 0))

    def _save_added_shape(self):
        new_value = self.shape_entry.get().strip()
        if not new_value:
            return

        shapes = self.shape_data.get_shapes()
        if new_value not in shapes:
            shapes.append(new_value)

        self.shape_entry.delete(0, tk.END)

        # Save to disk, then reload so the remove dropdown updates immediately.
        self.shape_data.save_shapes(shapes)

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        pass


class RemoveShapeOptionSection(ttk.LabelFrame):
    """Section for removing existing shapes from the trial shape option list."""

    def __init__(self, parent, shape_data: ShapeOptionsData, refresh_callback=None):
        super().__init__(parent, text="Remove shape option", padding=12)
        self.shape_data = shape_data
        self.refresh_callback = refresh_callback

        self.pack(fill="x", pady=(0, 12), anchor="w")

        ttk.Label(
            self,
            text="Choose a shape to remove it from the available shape options.",
            wraplength=1000,
            justify="left",
        ).pack(anchor="w", pady=(0, 6))

        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill="x", anchor="w")

        self.shape_dropdown = DropdownObject(
            controls_frame,
            "Shape",
            self._get_remove_options(),
            default_value="No selection",
            width=18,
        )
        self.shape_dropdown.pack(side="left", padx=(0, 12), anchor="n")

        save_button = ttk.Button(self, text="Save choices", command=self._save_removed_shape)
        save_button.pack(anchor="e", pady=(8, 0))

    def _get_remove_options(self):
        return ["No selection"] + self.shape_data.get_shapes()

    def _save_removed_shape(self):
        selected_value = self.shape_dropdown.get()
        if not selected_value or selected_value == "No selection":
            return

        shapes = self.shape_data.get_shapes()
        if selected_value in shapes:
            shapes.remove(selected_value)

        # Save the updated shape list back to disk so the removal persists.
        self.shape_data.save_shapes(shapes)

        if self.refresh_callback is not None:
            self.refresh_callback()

    def refresh(self):
        self.shape_dropdown.dropdown.configure(values=self._get_remove_options())
        self.shape_dropdown.set("No selection")


class ShapeClassifierSection(ttk.LabelFrame):
    """Device page section reserved for live shape classification controls."""

    def __init__(self, parent, device_getter=None):
        super().__init__(parent, text="Shape classifier", padding=12)
        self.device_getter = device_getter
        self.snapshot_backend = TrialSnapshotBackend()
        self.classifier_backend = ShapeClassifierBackend()

        self.pack(fill="x", pady=(15, 0), anchor="w")

        ttk.Button(self, text="Shape guess", command=self._guess_shape).pack(anchor="w")

        self.message_label = ttk.Label(
            self,
            text="",
            font=("Segoe UI", 36, "bold"),
            wraplength=1000,
            justify="left",
        )
        self.message_label.pack(anchor="w", pady=(8, 0))

    def _guess_shape(self):
        """Read the current live snapshot and classify it with the saved model."""
        device = self.device_getter() if self.device_getter is not None else None
        if device is None or not device.is_open or not device.running:
            self.message_label.config(text="Cannot guess shape: the device is not connected and running.", foreground="red")
            return

        relative_resistances = self.snapshot_backend.get_latest_relative_resistances(device)
        if relative_resistances is None:
            self.message_label.config(
                text="Need a complete 12-channel reading and a locked baseline before guessing.",
                foreground="red",
            )
            return

        try:
            guessed_shape = self.classifier_backend.predict_shape(relative_resistances)
        except FileNotFoundError:
            self.message_label.config(text="Cannot guess shape: saved classifier model is missing.", foreground="red")
            return
        except Exception:
            self.message_label.config(text="Shape could not be guessed from the current snapshot.", foreground="red")
            return

        self.message_label.config(text=f"Guessed shape: {guessed_shape}", foreground="black")


class DeviceTrialSection(ttk.LabelFrame):
    """Groups the trial snapshot capture and shape-option management on the Device page."""

    def __init__(self, parent, device_getter=None):
        super().__init__(parent, text="Trial data collection", padding=12)
        self.pack(fill="x", pady=(15, 0), anchor="w")

        self.shape_data = ShapeOptionsData()

        self.snapshot_section = AddTrialSnapshotSection(
            self, self.shape_data, self._refresh_sections, device_getter
        )
        self.remove_trial_section = RemoveTrialSnapshotSection(self, self._refresh_sections)
        self.add_shape_section = AddShapeOptionSection(self, self.shape_data, self._refresh_sections)
        self.remove_shape_section = RemoveShapeOptionSection(self, self.shape_data, self._refresh_sections)

    def _refresh_sections(self):
        self.snapshot_section.refresh()
        self.remove_trial_section.refresh()
        self.add_shape_section.refresh()
        self.remove_shape_section.refresh()
