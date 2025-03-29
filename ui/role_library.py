# ui/role_library.py
import os
import tkinter as tk
from tkinter import filedialog
import shutil
import re
import customtkinter as ctk
from tkinter import messagebox, BooleanVar
from customtkinter import CTkScrollableFrame, CTkTextbox, END
from utils import read_file, save_string_to_txt  # Import functions from utils
from novel_generator.common import invoke_with_cleaning  # New import
from prompt_definitions import Character_Import_Prompt

DEFAULT_FONT = ("latin modern roman", 12)

class RoleLibrary:
    def __init__(self, master, save_path, llm_adapter):  # Added llm_adapter parameter
        self.master = master
        self.save_path = os.path.join(save_path, "Role Library")
        self.selected_category = None
        self.current_roles = []
        self.selected_del = []
        self.llm_adapter = llm_adapter  # Save LLM adapter instance

        # Initialize the window
        self.window = ctk.CTkToplevel(master)
        self.window.title("Role Library Management")
        self.window.geometry("1200x800")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

        # Create directory structure
        self.create_library_structure()
        # Build UI
        self.create_ui()
        # Center the window
        self.center_window()
        # Set the window as modal
        self.window.grab_set()
        self.window.attributes('-topmost', 1)
        self.window.after(200, lambda: self.window.attributes('-topmost', 0))

    def create_library_structure(self):
        """Create necessary directory structure"""
        os.makedirs(self.save_path, exist_ok=True)
        all_dir = os.path.join(self.save_path, "All")
        os.makedirs(all_dir, exist_ok=True)

    def create_ui(self):
        """Create the main interface"""
        # Category button section
        self.create_category_bar()

        # Main content area
        main_frame = ctk.CTkFrame(self.window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel (remains unchanged)
        left_panel = ctk.CTkFrame(main_frame, width=300)
        left_panel.pack(side="left", fill="both", padx=5, pady=5)

        # Upper role list section (remains unchanged)
        role_list_container = ctk.CTkFrame(left_panel)
        role_list_container.pack(fill="both", expand=True, pady=(0, 5))

        self.role_list_frame = ctk.CTkScrollableFrame(role_list_container)
        self.role_list_frame.pack(fill="both", expand=True)

        # Lower content preview section (remains unchanged)
        preview_container = ctk.CTkFrame(left_panel)
        preview_container.pack(fill="both", expand=True, pady=(5, 0))

        self.preview_text = ctk.CTkTextbox(preview_container, wrap="word", font=("latin modern roman", 12))
        scrollbar = ctk.CTkScrollbar(preview_container, command=self.preview_text.yview)
        self.preview_text.configure(yscrollcommand=scrollbar.set)

        self.preview_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Right panel (information editing area)
        right_panel = ctk.CTkFrame(main_frame)
        right_panel.pack(side="right", fill="both", expand=True, padx=5, pady=5)

        # Category selection row
        category_frame = ctk.CTkFrame(right_panel)
        category_frame.pack(fill="x", padx=5, pady=5)

        # Category selection label
        ctk.CTkLabel(category_frame, text="Category Selection", font=DEFAULT_FONT).pack(side="left", padx=(0, 5))

        # Category selection combo box
        self.category_combobox = ctk.CTkComboBox(
            category_frame,
            values=self._get_all_categories(),
            width=200,
            font=DEFAULT_FONT
        )
        self.category_combobox.pack(side="left", padx=0)

        # Save category button
        self.save_category_btn = ctk.CTkButton(
            category_frame,
            text="Save Category",
            width=80,
            command=self._move_to_category,
            font=DEFAULT_FONT
        )
        self.save_category_btn.pack(side="left", padx=(0, 5))

        # Open folder button
        ctk.CTkButton(
            category_frame,
            text="Open Folder",
            width=80,
            command=lambda: os.startfile(
                os.path.join(self.save_path, self.category_combobox.get())),
            font=DEFAULT_FONT
        ).pack(side="left", padx=0)

        # Role name editing row
        name_frame = ctk.CTkFrame(right_panel)
        name_frame.pack(fill="x", padx=5, pady=5)

        # Role name label
        ctk.CTkLabel(name_frame, text="Role Name", font=DEFAULT_FONT).pack(side="left", padx=(0, 5))

        self.role_name_var = tk.StringVar()
        self.role_name_entry = ctk.CTkEntry(
            name_frame,
            textvariable=self.role_name_var,
            placeholder_text="Role Name",
            width=200,
            font=DEFAULT_FONT
        )
        self.role_name_entry.pack(side="left", padx=0)

        ctk.CTkButton(
            name_frame,
            text="Rename",
            width=60,
            command=self._rename_role_file,
            font=DEFAULT_FONT
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            name_frame,
            text="Add New",
            width=60,
            command=lambda: self._create_new_role("All"),
            font=DEFAULT_FONT
        ).pack(side="left", padx=0)

        # Attribute editing area (basic framework)
        self.attributes_frame = ctk.CTkScrollableFrame(right_panel)
        self.attributes_frame.pack(fill="both", expand=True, padx=5, pady=5)
        # Set uniform column weights
        self.attributes_frame.grid_columnconfigure(1, weight=1)

        button_frame = ctk.CTkFrame(right_panel)
        button_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(button_frame, text="Import Role",
                      command=self.import_roles, font=DEFAULT_FONT).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Delete",
                      command=self.delete_current_role, font=DEFAULT_FONT).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Save",
                      command=self.save_current_role, font=DEFAULT_FONT).pack(side="left", padx=5)

    def _get_all_categories(self):
        """Get all valid categories (including dynamic updates)"""
        categories = ["All"]
        for d in os.listdir(self.save_path):
            if os.path.isdir(os.path.join(self.save_path, d)) and d != "All":
                categories.append(d)
        return categories

    def _move_to_category(self):
        """Category transfer function"""
        if not hasattr(self, 'current_role') or not self.current_role:
            messagebox.showwarning("Warning", "Please select a role first", parent=self.window)
            return

        new_category = self.category_combobox.get()

        # If currently in "All" category, find the actual category of the role
        if self.selected_category == "All":
            # Iterate through all categories to find the actual storage location (including All directory)
            actual_category = None
            for category in os.listdir(self.save_path):
                test_path = os.path.join(
                    self.save_path, category, f"{self.current_role}.txt")
                if os.path.exists(test_path):
                    actual_category = category
                    break

            if not actual_category:
                msg = messagebox.showerror("Error", f"Could not find the actual storage location for role {self.current_role}", parent=self.window)
                self.window.attributes('-topmost', 1)
                msg.attributes('-topmost', 1)
                self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
                return

            old_path = os.path.join(
                self.save_path, actual_category, f"{self.current_role}.txt")
        else:
            old_path = os.path.join(
                self.save_path, self.selected_category, f"{self.current_role}.txt")

        # If the target category is "All", actually move to the "All" category
        if new_category == "All":
            new_path = os.path.join(
                self.save_path, "All", f"{self.current_role}.txt")
        else:
            new_path = os.path.join(
                self.save_path, new_category, f"{self.current_role}.txt")

        # Check if already in the target category
        if os.path.exists(new_path):
            msg = messagebox.showinfo("Info", "The role is already in the target category", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
            return

        confirm = messagebox.askyesno(
            "Confirm", f"Are you sure you want to move role {self.current_role} to {new_category} category?", parent=self.window)
        if not confirm:
            return

        try:
            # Ensure the target directory exists
            os.makedirs(os.path.dirname(new_path), exist_ok=True)

            try:
                # Perform the move operation
                shutil.move(old_path, new_path)

                # Update display
                self.selected_category = new_category if new_category != "All" else "All"
                self.show_category(self.selected_category)
                self.category_combobox.set(new_category)

                # Success message
                messagebox.showinfo("Success", "Category updated", parent=self.window)
                return  # Return directly on success

            except Exception as e:
                # On failure, restore the original category display
                self.category_combobox.set(self.selected_category)
                raise e
        except Exception as e:
            msg = messagebox.showerror("Error", f"Category transfer failed: {str(e)}", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
            self.category_combobox.set(self.selected_category)

    def import_roles(self):
        """Import role window"""
        import_window = ctk.CTkToplevel(self.window)
        import_window.title("Import Roles")
        import_window.geometry("800x600")
        import_window.transient(self.window)  # Set as child window
        import_window.grab_set()  # Modal window
        import_window.lift()  # Bring to the front

        # Center the window
        import_window.update_idletasks()
        i_width = import_window.winfo_width()
        i_height = import_window.winfo_height()
        x = self.window.winfo_x() + (self.window.winfo_width() - i_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - i_height) // 2
        import_window.geometry(f"+{x}+{y}")

        # Main content area
        main_frame = ctk.CTkFrame(import_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left-right panel container
        content_frame = ctk.CTkFrame(main_frame)
        content_frame.pack(fill="both", expand=True, pady=(0, 10))
        content_frame.grid_columnconfigure(0, weight=1)  # Left panel weight
        content_frame.grid_columnconfigure(1, weight=1)  # Right panel weight

        # Left panel - use weights to make widgets fill space
        left_panel = ctk.CTkFrame(content_frame)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        left_panel.grid_rowconfigure(0, weight=1)
        left_panel.grid_columnconfigure(0, weight=1)
        left_panel.grid_propagate(False)  # Prevent child widgets from changing parent container size

        # Right panel (2-column width) - Add initial editable text box
        right_panel = ctk.CTkFrame(content_frame)
        right_panel.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # Create initial editable text box
        text_box = ctk.CTkTextbox(right_panel, wrap="word", font=DEFAULT_FONT)
        text_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        text_box.configure(state="normal")  # Keep editable state

        # Initialize the import roles list
        self.import_roles_list = []

        # Bottom button area
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(0, 10))

        # Import button
        ctk.CTkButton(
            btn_frame,
            text="Import Temporary Role Library",
            width=120,
            command=lambda: self.confirm_import(import_window),
            font=DEFAULT_FONT
        ).pack(side="left", padx=10)

        # Analyze file button
        ctk.CTkButton(
            btn_frame,
            text="Analyze File",
            width=100,
            command=lambda: self.analyze_character_state(right_panel, left_panel),
            font=DEFAULT_FONT
        ).pack(side="left", padx=10)

        # Load character_state.txt button
        ctk.CTkButton(
            btn_frame,
            text="Load character_state.txt",
            width=160,
            command=lambda: self.load_default_character_state(right_panel),
            font=DEFAULT_FONT
        ).pack(side="right", padx=10)

        # Import from file button
        ctk.CTkButton(
            btn_frame,
            text="Import from File",
            width=100,
            command=lambda: self.import_from_file(right_panel),
            font=DEFAULT_FONT
        ).pack(side="right", padx=10)

        # Set content area weight
        content_frame.grid_rowconfigure(0, weight=1)

    def analyze_character_state(self, right_panel, left_panel):
        """Analyze character state file, use LLM to extract character information and save to temporary role library"""
        content = ""
        for widget in right_panel.winfo_children():
            if isinstance(widget, ctk.CTkTextbox):
                content = widget.get("1.0", "end").strip()
                break

        if not content:
            messagebox.showwarning("Warning", "No content to analyze", parent=self.window)
            return

        try:
            # Create temporary role library directory
            target_dir = os.path.join(self.save_path, "Temporary Role Library")
            # Clear existing temporary role library
            if os.path.exists(target_dir):
                for filename in os.listdir(target_dir):
                    file_path = os.path.join(target_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
            os.makedirs(target_dir, exist_ok=True)

            # Call LLM for analysis
            prompt = f"{Character_Import_Prompt}\n<<Start of novel text>>\n{content}\n<<End of novel text>>"
            response = invoke_with_cleaning(
                self.llm_adapter,
                prompt
            )

            # Parse LLM response
            roles = self._parse_llm_response(response)

            if not roles:
                messagebox.showwarning("Warning", "No valid character information found", parent=self.window)
                return

            # Directly display analyzed roles without saving to file
            self._display_analyzed_roles(left_panel, roles)

        except Exception as e:
            messagebox.showerror("Analysis Failed", f"LLM analysis error: {str(e)}", parent=self.window)
    
    def _display_temp_roles(self, parent, temp_dir):
        """Display roles in the temporary role library"""
        # Clear the left panel
        for widget in parent.winfo_children():
            widget.destroy()

        # Create a scrollable container
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True)

        # Read all temporary role files
        self.character_checkboxes = {}
        for file_name in os.listdir(temp_dir):
            if file_name.endswith(".txt"):
                role_name = os.path.splitext(file_name)[0]
                file_path = os.path.join(temp_dir, file_name)

                # Parse role attributes
                attributes = self._parse_temp_role_file(file_path)

                # Create items with checkboxes
                frame = ctk.CTkFrame(scroll_frame)
                frame.pack(fill="x", pady=2, padx=5)

                # Checkbox
                var = BooleanVar(value=True)
                cb = ctk.CTkCheckBox(frame, text="", variable=var, width=20, font=DEFAULT_FONT)
                cb.pack(side="left", padx=5)

                # Role name
                lbl = ctk.CTkLabel(frame, text=role_name, 
                                font=("latin modern roman", 12))
                lbl.pack(side="left", padx=5)

                # Attribute summary
                attrs = [f"{k}({len(v)})" for k, v in attributes.items()]
                summary = ctk.CTkLabel(frame, text=" | ".join(attrs), 
                                    font=("latin modern roman", 12),
                                    text_color="gray")
                summary.pack(side="right", padx=10)

                self.character_checkboxes[role_name] = {
                    'var': var,
                    'data': {'name': role_name, 'attributes': attributes}
                }

        # Add operation buttons
        btn_frame = ctk.CTkFrame(scroll_frame)
        btn_frame.pack(fill="x", pady=5)
        ctk.CTkButton(btn_frame, text="Select All", 
                    command=lambda: self._toggle_all(True), font=DEFAULT_FONT).pack(side="left")
        ctk.CTkButton(btn_frame, text="Deselect All", 
                    command=lambda: self._toggle_all(False), font=DEFAULT_FONT).pack(side="left")

    def _parse_temp_role_file(self, file_path):
        """Parse temporary role file"""
        attributes = {}
        current_attr = None
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    # Uniform parsing for ├── and └── prefixes
                    if any(prefix in line for prefix in ['├──', '└──']) and '：' in line:
                        prefix = '├──' if '├──' in line else '└──'
                        current_attr = line.split(prefix)[1].split('：')[0].strip()
                        attributes[current_attr] = []
                    elif any(prefix in line for prefix in ['│  ├──', '│  └──']):
                        prefix = '│  ├──' if '│  ├──' in line else '│  └──'
                        if current_attr:
                            item = line.split(prefix)[1].strip()
                            attributes[current_attr].append(item)
        except Exception as e:
            messagebox.showerror("Parsing Error", f"Failed to parse temporary file: {str(e)}", parent=self.window)
        return attributes

    def _parse_llm_response(self, response):
        """Parse role data returned by LLM"""
        roles = []
        current_role = None
        current_attr = None
        current_subattr = None

        attribute_pattern = re.compile(r'^([├└]──)([\w\u4e00-\u9fa5]+)\s*[:：]')
        item_pattern = re.compile(r'^│\s+([├└]──)\s*(.*)')

        for line in response.split('\n'):
            line = line.rstrip()

            # Detect role name line (compatible with both Chinese and English colons and spaces)
            role_match = re.match(r'^\s*([\u4e00-\u9fa5a-zA-Z0-9]+)\s*[:：]\s*$', line)
            if role_match:
                current_role = role_match.group(1).strip()
                roles.append({'name': current_role, 'attributes': {}})
                continue

            if not current_role:
                continue

            # Parse attributes (supports subattributes)
            attr_match = attribute_pattern.match(line)
            if attr_match:
                prefix, attr_name = attr_match.groups()
                current_attr = attr_name.strip()
                roles[-1]['attributes'][current_attr] = []
                current_subattr = None
                continue

            # Parse attribute items (supports multi-level structure)
            item_match = item_pattern.match(line)
            if item_match and current_attr:
                prefix, content = item_match.groups()
                content = content.strip()

                # Parse subattributes (e.g., "Body status: xxx")
                if ':' in content or '：' in content:
                    subattr_match = re.split(r'[:：]', content, 1)
                    if len(subattr_match) > 1:
                        current_subattr = subattr_match[0].strip()
                        value = subattr_match[1].strip()
                        if value:  # Only add if the value is not empty
                            roles[-1]['attributes'][current_attr].append(
                                f"{current_subattr}: {value}"
                            )
                        continue

                # Handle regular entries
                if content:
                    if current_subattr:
                        # Continuation of a subattribute
                        roles[-1]['attributes'][current_attr][-1] += f", {content}"
                    else:
                        roles[-1]['attributes'][current_attr].append(content)
        return roles

    def _display_analyzed_roles(self, parent, roles):
        """Display the analyzed role list"""
        self.character_checkboxes = {}

        # Create a scrollable container
        scroll_frame = ctk.CTkScrollableFrame(parent)
        scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_frame.grid_rowconfigure(0, weight=1)
        scroll_frame.grid_columnconfigure(0, weight=1)

        # Create items with checkboxes for each role
        for role in roles:
            frame = ctk.CTkFrame(scroll_frame)
            frame.pack(fill="x", pady=2, padx=5)

            # Checkbox
            var = BooleanVar(value=True)
            cb = ctk.CTkCheckBox(frame, text="", variable=var, width=20, font=DEFAULT_FONT)
            cb.pack(side="left", padx=5)

            # Role name label
            lbl = ctk.CTkLabel(frame, text=role['name'], 
                            font=("latin modern roman", 12))
            lbl.pack(side="left", padx=5)

            # Attribute summary
            attrs = [f"{k}({len(v)})" for k, v in role['attributes'].items()]
            summary = ctk.CTkLabel(frame, text=" | ".join(attrs), 
                                font=("latin modern roman", 12),
                                text_color="gray")
            summary.pack(side="right", padx=10)

            self.character_checkboxes[role['name']] = {
                'var': var,
                'data': role
            }

        # Add select/deselect all buttons
        btn_frame = ctk.CTkFrame(scroll_frame)
        btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Select All", 
                    command=lambda: self._toggle_all(True), font=DEFAULT_FONT).pack(side="left")
        ctk.CTkButton(btn_frame, text="Deselect All", 
                    command=lambda: self._toggle_all(False), font=DEFAULT_FONT).pack(side="left")

    def _toggle_all(self, select):
        """Select/Deselect All operation"""
        for role in self.character_checkboxes.values():
            current_state = role['var'].get()
            # If it is deselect operation, set the opposite state
            if isinstance(select, bool):
                role['var'].set(select)
            else:
                role['var'].set(not current_state)

    def import_from_file(self, right_panel):
        """Import content from a file into the right panel"""
        filetypes = (
            ('Text files', '*.txt'),
            ('Word documents', '*.docx'),
            ('All files', '*.*')
        )

        file_path = filedialog.askopenfilename(
            title="Select the file to import",
            initialdir=os.path.expanduser("~"),
            filetypes=filetypes
        )

        if not file_path:
            return

        try:
            content = ""
            if file_path.endswith('.docx'):
                # Process Word document
                from docx import Document
                doc = Document(file_path)
                content = "\n".join([para.text for para in doc.paragraphs])
            else:
                # Process regular text file
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            # Update the right panel's text box
            for widget in right_panel.winfo_children():
                if isinstance(widget, ctk.CTkTextbox):
                    widget.delete("1.0", "end")
                    widget.insert("1.0", content)
                    break

        except Exception as e:
            messagebox.showerror("Import Failed", f"Cannot read the file: {str(e)}", parent=self.window)

    def load_default_character_state(self, right_panel):
        """Load the character_state.txt file into the right panel"""
        # Get save path
        save_path = os.path.dirname(self.save_path)
        file_path = os.path.join(save_path, "character_state.txt")

        if not os.path.exists(file_path):
            messagebox.showwarning("Warning", f"File not found: {file_path}", parent=self.window)
            return

        try:
            # Read file content
            content = read_file(file_path)

            # Clear existing widgets in the right panel
            for widget in right_panel.winfo_children():
                widget.destroy()

            # Find or create a textbox
            text_box = None
            for widget in right_panel.winfo_children():
                if isinstance(widget, ctk.CTkTextbox):
                    text_box = widget
                    break

            if not text_box:
                text_box = ctk.CTkTextbox(right_panel, wrap="word", font=("latin modern roman", 12))
                text_box.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

            text_box.configure(state="normal")
            text_box.delete("1.0", "end")
            text_box.insert("1.0", content)

            # Set layout weight for the right panel
            right_panel.grid_rowconfigure(0, weight=1)
            right_panel.grid_columnconfigure(0, weight=1)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load the file: {str(e)}", parent=self.window)

    def confirm_import(self, import_window):
        """Import selected roles from the temporary role library"""
        # Create necessary directory
        target_dir = os.path.join(self.save_path, "Temporary Role Library")
        os.makedirs(target_dir, exist_ok=True)

        try:
            # Get selected roles
            selected_roles = [role_data['data'] for role_data in self.character_checkboxes.values() 
                            if role_data['var'].get()]

            if not selected_roles:
                # Create error window
                error_window = ctk.CTkToplevel(import_window)
                error_window.title("Error")
                error_window.transient(import_window)
                error_window.grab_set()

                # Window content
                ctk.CTkLabel(error_window, text="Please select at least one role", font=("latin modern roman", 12)).pack(padx=20, pady=10)
                ctk.CTkButton(error_window, text="OK", command=error_window.destroy, font=("latin modern roman", 12)).pack(pady=10)

                # Center the window
                error_window.update_idletasks()
                e_width = error_window.winfo_width()
                e_height = error_window.winfo_height()
                x = import_window.winfo_x() + (import_window.winfo_width() - e_width) // 2
                y = import_window.winfo_y() + (import_window.winfo_height() - e_height) // 2
                error_window.geometry(f"+{x}+{y}")
                error_window.attributes('-topmost', 1)
                return

            # Save roles from memory directly
            for role in selected_roles:
                dest_path = os.path.join(target_dir, f"{role['name']}.txt")

                # Build role content
                content_lines = [f"{role['name']}:"]
                for attr, items in role['attributes'].items():
                    content_lines.append(f"├──{attr}:")
                    for i, item in enumerate(items):
                        prefix = "├──" if i < len(items)-1 else "└──"
                        content_lines.append(f"│  {prefix}{item}")

                # Write to file, overwrite if file exists
                with open(dest_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content_lines))

            # Refresh category display
            self.load_categories()
            import_window.destroy()

        except Exception as e:
            # Silently handle error
            import_window.destroy()

    def delete_current_role(self):
        """Delete the current role"""
        if not hasattr(self, 'current_role') or not self.current_role:
            return

        confirm = messagebox.askyesno(
            "Confirm Delete", f"Are you sure you want to delete the role {self.current_role}?", parent=self.window)
        if not confirm:
            return

        role_path = os.path.join(
            self.save_path, self.selected_category, f"{self.current_role}.txt")
        try:
            os.remove(role_path)
            # Also delete from "All" category
            all_path = os.path.join(
                self.save_path, "All", f"{self.current_role}.txt")
            if os.path.exists(all_path):
                os.remove(all_path)
            self.show_category(self.selected_category)
            self.preview_text.delete("1.0", "end")
            msg = messagebox.showinfo("Success", "Role has been deleted", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
        except Exception as e:
            msg = messagebox.showerror("Error", f"Failed to delete: {str(e)}", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])

    def _build_role_content(self):
        """Build content for the role file"""
        content = [f"{self.role_name_var.get()}:"]
        attributes_order = ["Items", "Abilities", "Status", "Main Role Relationships", "Events Triggered or Deepened"]

        for attr_name in attributes_order:
            content.append(f"├──{attr_name}:")
            # Find corresponding attribute block
            for block in self.attributes_frame.winfo_children():
                if isinstance(block, ctk.CTkFrame) and block.attribute_name == attr_name:
                    # Traverse all CTkEntry within the block
                    for child in block.winfo_children():
                        if isinstance(child, ctk.CTkFrame):  # Entry row
                            for item in child.winfo_children():
                                if isinstance(item, ctk.CTkEntry):
                                    entry_text = item.get().strip()
                                    if entry_text:  # Only add non-empty entries
                                        content.append(f"│  ├──{entry_text}")
                    break  # Break when the corresponding attribute is found
        return content

    def _save_role_file(self, content, save_path):
        """Save role file"""
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

    def _check_role_name_conflict(self, new_name):
        """Check for role name conflicts across all category folders"""
        conflicts = []
        # Traverse all category directories
        for category in os.listdir(self.save_path):
            if os.path.isdir(os.path.join(self.save_path, category)):
                # Check if the category contains a role with the same name
                role_path = os.path.join(
                    self.save_path, category, f"{new_name}.txt")
                if os.path.exists(role_path):
                    # If it is in the "All" category, check if it's an actual file
                    if category == "All":
                        # Check if the file in the "All" directory is an actual file
                        all_path = os.path.join(
                            self.save_path, "All", f"{new_name}.txt")
                        if os.path.isfile(all_path):
                            # If it is an actual file, it is considered a conflict
                            conflicts.append(category)
                    else:
                        # For normal categories, directly record the conflict
                        conflicts.append(category)
        return conflicts

    def save_current_role(self):
        """Save the currently edited role"""
        if not hasattr(self, 'current_role') or not self.current_role:
            return

        new_name = self.role_name_var.get().strip()
        if not new_name:
            msg = messagebox.showwarning("Warning", "Role name cannot be empty", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
            return

        # Check for role name conflicts
        if new_name != self.current_role:
            conflicts = self._check_role_name_conflict(new_name)
            if conflicts:
                messagebox.showerror("Error",       
                                    f"The role name '{new_name}' already exists in the following categories:\n" +
                                    "\n".join(conflicts) +
                                    "\nPlease use a different role name", parent=self.window)
                return

        content = self._build_role_content()
        save_path = os.path.join(self.save_path, self.selected_category,
                                f"{new_name}.txt")

        try:
            self._save_role_file(content, save_path)
            # If the role name is changed, update the file name
            if new_name != self.current_role:
                old_path = os.path.join(self.save_path, self.selected_category,
                                        f"{self.current_role}.txt")
                os.rename(old_path, save_path)

            # Update display
            self.current_role = new_name
            self.show_category(self.selected_category)
            self.show_role(new_name)  # Refresh role display
            messagebox.showinfo("Success", "Role has been saved", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}", parent=self.window)

    def _rename_role_file(self):
        """Rename the role"""
        old_name = self.current_role
        new_name = self.role_name_var.get().strip()

        if not old_name or not new_name:
            return

        # Handle colon in both Chinese and English forms
        for colon in [":", "："]:
            old_name = old_name.split(colon)[0]
            new_name = new_name.split(colon)[0]

        # If the role name has not changed, return
        if new_name == old_name:
            return

        # Check for role name conflicts
        conflicts = self._check_role_name_conflict(new_name)
        if conflicts:
            messagebox.showerror("Error",
                                f"The role name '{new_name}' already exists in the following categories:\n" +
                                "\n".join(conflicts) +
                                "\nPlease use a different role name", parent=self.window)
            return

        try:
            # If it's the "All" category, find the actual storage category
            if self.selected_category == "All":
                # First, check if the file exists in the "All" directory
                all_path = os.path.join(self.save_path, "All", f"{old_name}.txt")
                if os.path.exists(all_path):
                    # If the file exists in the "All" directory, directly operate on it
                    actual_category = "All"
                else:
                    # Traverse all categories to find the actual storage location
                    actual_category = None
                    for category in os.listdir(self.save_path):
                        if category == "All":
                            continue
                        test_path = os.path.join(self.save_path, category, f"{old_name}.txt")
                        if os.path.exists(test_path):
                            actual_category = category
                            break

                    if not actual_category:
                        raise FileNotFoundError(
                            f"Could not find the actual storage location for role {old_name}")
            else:
                actual_category = self.selected_category

            # Read the old file content and update the role name
            old_path = os.path.join(self.save_path, actual_category, f"{old_name}.txt")
            with open(old_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Get the first line content
            first_line = content.split('\n')[0].strip()
            # Extract the role name from the content
            content_role_name = first_line.split('：')[0].split(':')[0].strip()
            # If the content's role name is different from the old file name, update the content
            if content_role_name != old_name:
                content = content.replace(
                    f"{content_role_name}：", f"{new_name}：", 1)
            else:
                content = content.replace(f"{old_name}：", f"{new_name}：", 1)

            # Write the updated content to the new file
            new_path = os.path.join(self.save_path, actual_category, f"{new_name}.txt")
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Delete the old file
            os.remove(old_path)

            # Handle the "All" directory
            all_old_path = os.path.join(self.save_path, "All", f"{old_name}.txt")
            all_new_path = os.path.join(self.save_path, "All", f"{new_name}.txt")

            # If the old file exists in the "All" directory
            if os.path.exists(all_old_path):
                try:
                    # Update the file content in the "All" directory
                    with open(all_old_path, 'r', encoding='utf-8') as f:
                        all_content = f.read()
                    updated_all_content = all_content.replace(
                        f"{old_name}：", f"{new_name}：", 1)

                    # Write the updated content to the new file
                    with open(all_new_path, 'w', encoding='utf-8') as f:
                        f.write(updated_all_content)

                    # Delete the old file from the "All" directory
                    os.remove(all_old_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to update the 'All' directory: {str(e)}", parent=self.window)
                    # Rollback the rename operation
                    os.rename(new_path, old_path)
                    return

            # Refresh the display
            self.current_role = new_name
            self.show_category(self.selected_category)
            self.role_name_var.set(new_name)
            self.show_role(new_name)  # Refresh the role display

        except Exception as e:
            msg = messagebox.showerror("Error", f"Rename failed: {str(e)}", parent=self.window)
            self.window.attributes('-topmost', 1)
            msg.attributes('-topmost', 1)
            self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])

    def _create_new_role(self, category):
        """Create a new role in the specified category"""
        role_dir = os.path.join(self.save_path, category)
        base_name = "Untitled"
        counter = 1

        # Generate a unique file name
        while os.path.exists(os.path.join(role_dir, f"{base_name}.txt")):
            base_name = f"Untitled{counter}"
            counter += 1

        # Create the basic file structure (with initial entries)
        content = f"{base_name}：\n" + "\n".join([
            "├──Items:",
            "│  └──To be added",
            "├──Abilities:",
            "│  └──To be added",
            "├──Status:",
            "│  └──To be added",
            "├──Main Role Relationships:",
            "│  └──To be added",
            "├──Events Triggered or Deepened:",
            "│  └──To be added"
        ])

        with open(os.path.join(role_dir, f"{base_name}.txt"), "w", encoding="utf-8") as f:
            f.write(content)

        # Refresh the display
        self.show_category(category)
        self.role_name_var.set(base_name)
        self.current_role = base_name

    def create_category_bar(self):
        """Create the category button area"""
        category_frame = ctk.CTkFrame(self.window)
        category_frame.pack(fill="x", padx=10, pady=5)

        # Instruction
        ctk.CTkLabel(category_frame,
                    text="Right-click category name to rename",
                    font=("latin modern roman", 12),
                    text_color="gray").pack(side="top", anchor="w", padx=5)

        # Fixed buttons
        ctk.CTkButton(category_frame, text="All", width=50,
                    font=("latin modern roman", 12),
                    command=lambda: self.show_category("All")).pack(side="left", padx=2)

        # Scrollable category area
        self.scroll_frame = ctk.CTkScrollableFrame(
            category_frame, orientation="horizontal", height=30)
        self.scroll_frame.pack(side="left", fill="x", expand=True, padx=5)

        # Action buttons
        ctk.CTkButton(category_frame, text="Add", width=50,
                    command=self.add_category, font=("latin modern roman", 12)).pack(side="right", padx=2)
        ctk.CTkButton(category_frame, text="Delete", width=50,
                    command=self.delete_category, font=("latin modern roman", 12)).pack(side="right", padx=2)

        self.load_categories()

    def center_window(self):
        """Center the window"""
        self.window.update_idletasks()
        parent_x = self.master.winfo_x()
        parent_y = self.master.winfo_y()
        parent_width = self.master.winfo_width()
        parent_height = self.master.winfo_height()
        win_width = 1200
        win_height = 800
        x = parent_x + (parent_width - win_width) // 2
        y = parent_y + (parent_height - win_height) // 2
        self.window.geometry(f"{win_width}x{win_height}+{x}+{y}")

    def load_categories(self):
        """Load category buttons"""
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        categories = [d for d in os.listdir(self.save_path)
                    if os.path.isdir(os.path.join(self.save_path, d)) and d != "All"]

        for category in categories:
            btn = ctk.CTkButton(self.scroll_frame, text=category, width=80, font=("latin modern roman", 12))
            btn.bind("<Button-1>", lambda e, c=category: self.show_category(c))
            btn.bind("<Button-3>", lambda e, c=category: self.rename_category(c))
            btn.pack(side="left", padx=2)

    def _create_category_directory(self, category_name):
        """Create category directory"""
        new_dir = os.path.join(self.save_path, category_name)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        return new_dir

    def add_category(self):
        """Add new category"""
        self._create_category_directory("Untitled")
        self.load_categories()
        # Refresh category selection dropdown
        self.category_combobox.configure(values=self._get_all_categories())

    def delete_category(self):
        """Delete category dialog"""
        if not self.window.winfo_exists():
            return

        del_window = ctk.CTkToplevel(self.window)
        del_window.title("Delete Category")
        del_window.transient(self.window)
        del_window.grab_set()
        del_window.attributes('-topmost', 1)

        # Center calculation
        parent_x = self.window.winfo_x()
        parent_y = self.window.winfo_y()
        parent_width = self.window.winfo_width()
        parent_height = self.window.winfo_height()
        del_window.geometry(
            f"300x400+{parent_x + (parent_width-300)//2}+{parent_y + (parent_height-400)//2}")

        scroll_frame = ctk.CTkScrollableFrame(del_window)
        scroll_frame.pack(fill="both", expand=True)

        categories = [d for d in os.listdir(self.save_path)
                    if os.path.isdir(os.path.join(self.save_path, d)) and d != "All"]
        self.selected_del = []

        for cat in categories:
            var = tk.BooleanVar()
            chk = ctk.CTkCheckBox(scroll_frame, text=cat, variable=var, font=("latin modern roman", 12))
            chk.pack(anchor="w")
            self.selected_del.append((cat, var))

        # Action buttons
        btn_frame = ctk.CTkFrame(del_window)
        btn_frame.pack(fill="x", pady=5)

        ctk.CTkButton(btn_frame, text="Delete Selected",
                    command=lambda: self.confirm_delete(del_window), font=("latin modern roman", 12)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Cancel",
                    command=del_window.destroy, font=("latin modern roman", 12)).pack(side="right", padx=5)

        self.category_combobox.configure(values=self._get_all_categories())
        self.category_combobox.set("All")

    def confirm_delete(self, original_window):
        """Confirm delete operation"""
        selected = [item[0] for item in self.selected_del if item[1].get()]
        if not selected:
            msg = messagebox.showwarning("Warning", "Please select at least one category", parent=self.window)
            self.window.attributes('-topmost', 1)
            self.window.after(200, lambda: self.window.attributes('-topmost', 0))
            return

        # Create the choice window with setup
        choice_window = ctk.CTkToplevel(self.window)
        choice_window.transient(self.window)  # Set as a child window
        choice_window.grab_set()  # Modal window
        choice_window.lift()  # Bring to the front
        choice_window.attributes('-topmost', 1)  # Force topmost

        # Add center calculation
        choice_window.update_idletasks()
        c_width = choice_window.winfo_width()
        c_height = choice_window.winfo_height()
        x = self.window.winfo_x() + (self.window.winfo_width() - c_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - c_height) // 2
        choice_window.geometry(f"+{x}+{y}")

        ctk.CTkLabel(choice_window, text="Please choose a deletion method:", font=("latin modern roman", 12)).pack(pady=10)
        btn_frame = ctk.CTkFrame(choice_window)
        btn_frame.pack(pady=10)

        def perform_delete(mode):
            all_dir = os.path.join(self.save_path, "All")
            for cat in selected:
                cat_path = os.path.join(self.save_path, cat)
                if mode == "move":
                    for role_file in os.listdir(cat_path):
                        if role_file.endswith(".txt"):
                            src = os.path.join(cat_path, role_file)
                            dst = os.path.join(all_dir, role_file)
                            try:
                                shutil.move(src, dst)
                            except:
                                os.remove(dst)
                                shutil.move(src, dst)
                shutil.rmtree(cat_path)
            self.load_categories()
            # Refresh category selection dropdown
            self.category_combobox.configure(values=self._get_all_categories())
            original_window.destroy()
            choice_window.destroy()

        ctk.CTkButton(btn_frame, text="Delete All",
                    command=lambda: perform_delete("all"), font=("latin modern roman", 12)).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Move Roles",
                    command=lambda: perform_delete("move"), font=("latin modern roman", 12)).pack(side="left", padx=5)

    def count_roles(self, categories):
        """Count the number of roles"""
        count = 0
        for cat in categories:
            cat_path = os.path.join(self.save_path, cat)
            count += len([f for f in os.listdir(cat_path) if f.endswith(".txt")])
        return count

    def show_category(self, category):
        """Show category contents"""
        self.selected_category = category
        self.category_combobox.set(category)
        for widget in self.role_list_frame.winfo_children():
            widget.destroy()

        # If it's the "All" category, show all roles
        if category == "All":
            # Get all category directories
            categories = [d for d in os.listdir(self.save_path)
                          if os.path.isdir(os.path.join(self.save_path, d))]
            # Used for deduplication of roles
            unique_roles = set()

            for cat in categories:
                role_dir = os.path.join(self.save_path, cat)
                try:
                    for role_file in os.listdir(role_dir):
                        if role_file.endswith(".txt"):
                            role_name = os.path.splitext(role_file)[0]
                            # Deduplication
                            if role_name not in unique_roles:
                                unique_roles.add(role_name)
                                btn = ctk.CTkButton(
                                    self.role_list_frame,
                                    text=role_name,
                                    command=lambda r=role_name: self.show_role(r),
                                    font=("Latin Modern Roman", 12)
                                )
                                btn.pack(fill="x", pady=2)
                except FileNotFoundError:
                    continue
        else:
            # Normal category display
            role_dir = os.path.join(self.save_path, category)
            try:
                for role_file in os.listdir(role_dir):
                    if role_file.endswith(".txt"):
                        role_name = os.path.splitext(role_file)[0]
                        btn = ctk.CTkButton(
                            self.role_list_frame,
                            text=role_name,
                            command=lambda r=role_name: self.show_role(r),
                            font=("Latin Modern Roman", 12)
                        )
                        btn.pack(fill="x", pady=2)
            except FileNotFoundError:
                messagebox.showerror("Error", "Category directory not found", parent=self.window)

    def show_role(self, role_name):
        """Show detailed role information (supports UTF-8/ANSI encoding)"""
        try:
            # Clear existing attribute controls
            self.preview_text.delete('1.0', tk.END)
            for widget in self.attributes_frame.winfo_children():
                widget.destroy()

            # Update role name display
            self.current_role = role_name.split(":")[0].split("：")[0]
            self.role_name_var.set(self.current_role)

            # Find the actual directory of the role
            if self.selected_category == "All":
                # First check if the role file exists in the "All" directory
                all_path = os.path.join(
                    self.save_path, "All", f"{role_name}.txt")
                if os.path.exists(all_path):
                    file_path = all_path
                    actual_category = "All"
                else:
                    # If not found in "All", search in other categories
                    file_path = None
                    for cat in os.listdir(self.save_path):
                        if cat == "All":
                            continue
                        test_path = os.path.join(
                            self.save_path, cat, f"{role_name}.txt")
                        if os.path.exists(test_path):
                            file_path = test_path
                            actual_category = cat
                            # Save the actual category
                            self.actual_category = cat
                            break
                    if file_path is None:
                        raise FileNotFoundError(f"Role file not found: {role_name}")

                # Only update the category combobox display value, without changing the selected category
                self.category_combobox.set(actual_category)
            else:
                # Normal category, directly use the current path
                file_path = os.path.join(
                    self.save_path, self.selected_category, f"{role_name}.txt")

            content, _ = self._read_file_with_fallback_encoding(file_path)

            # Parse attribute structure
            attributes = {
                "Items": [],
                "Abilities": [],
                "Status": [],
                "Main Role Relationships": [],
                "Events that trigger or deepen": []
            }
            current_attribute = None
            for line in content[1:]:
                # Improve attribute name recognition
                if line.startswith(("├──", "├──")):
                    # Extract attribute name (compatible with colon and spaces)
                    attr_part = line.split("──")[1].strip()
                    attr_name = re.split(r'[:：]', attr_part, 1)[0].strip()

                    # Match preset attributes
                    for preset_attr in attributes:
                        if attr_name == preset_attr:
                            current_attribute = preset_attr
                            indent_level = line.find(
                                "├") if "├" in line else line.find("├")
                            break
                    else:
                        current_attribute = None

                # Improve item content extraction
                elif current_attribute and line.startswith(("│  ", "   ")):
                    # Extract entire item content
                    item_content = line.strip()
                    # Remove leading symbols and spaces
                    item_content = re.sub(r'^[│├└─\s]*', '', item_content)
                    attributes[current_attribute].append(item_content)

            # Display the raw file content
            self.preview_text.insert(tk.END, '\n'.join(content))

            # Reconstruct the attribute editing section
            for attr_name, items in attributes.items():
                self._create_attribute_section(attr_name, items)

        except FileNotFoundError as e:
            messagebox.showerror("Error", f"File not found: {e}", parent=self.window)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read file: {e}", parent=self.window)

    def _create_attribute_section(self, attr_name, items):
        """Create an editing area for a single attribute"""

        # Attribute block (attribute_block)
        attribute_block = ctk.CTkFrame(self.attributes_frame)
        attribute_block.pack(fill="x", pady=5)
        attribute_block.attribute_name = attr_name  # Store attribute name
        attribute_block.grid_columnconfigure(1, weight=1)  # Set second column weight
        attribute_block.grid_columnconfigure(1, weight=1)  # Set second column weight

        # Attribute name label
        label = ctk.CTkLabel(attribute_block, text=attr_name, font=("Latin Modern Roman", 12))
        label.grid(row=0, column=0, sticky="w", padx=(5, 10), pady=2)

        # First item and "Add" button container
        first_item_frame = ctk.CTkFrame(attribute_block)
        first_item_frame.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        first_item_frame.grid_columnconfigure(0, weight=1)

        # First item input box
        first_entry = ctk.CTkEntry(first_item_frame, font=("Latin Modern Roman", 12))
        first_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipadx=5, ipady=3)
        if items:
            first_entry.insert(0, items[0])  # Fill the first item's content

        # "Add" button container
        add_button_frame = ctk.CTkFrame(first_item_frame, fg_color="transparent")
        add_button_frame.grid(row=0, column=1, sticky="e", padx=(5, 0))

        # "Add" button
        add_button = ctk.CTkButton(
            add_button_frame,
            text="+",
            width=30,
            command=lambda: self._add_item(attr_name),
            font=("Latin Modern Roman", 12)
        )
        add_button.grid(row=0, column=0)

        # Create remaining items (if any)
        for i, item_text in enumerate(items[1:]):
            self._add_item(attr_name, item_text)  # Pass initial text

    def _add_item(self, attr_name, initial_text=""):
        """Add a new item for the specified attribute"""

        # Find corresponding attribute block
        attribute_block = None
        for block in self.attributes_frame.winfo_children():
            if isinstance(block, ctk.CTkFrame) and block.attribute_name == attr_name:
                attribute_block = block
                break

        if attribute_block is None:
            return

        # Calculate the row number for the new item
        row_number = 0
        for child in attribute_block.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                row_number += 1

        # Item container
        item_frame = ctk.CTkFrame(attribute_block)
        item_frame.grid(row=row_number, column=1, sticky="ew", padx=5, pady=2)
        item_frame.grid_columnconfigure(0, weight=1)

        # Item input box
        new_entry = ctk.CTkEntry(item_frame, font=("Latin Modern Roman", 12))
        new_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5), ipadx=5, ipady=3)
        new_entry.insert(0, initial_text)  # Set initial text

        # Delete button container
        del_button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        del_button_frame.grid(row=0, column=1, sticky="e", padx=(5, 0))
        # "Delete" button
        del_button = ctk.CTkButton(
            del_button_frame,
            text="-",
            width=30,
            command=lambda f=item_frame: self._remove_item(f, attr_name),
            font=("Latin Modern Roman", 12)
        )
        del_button.grid(row=0, column=0)


    def _remove_item(self, item_frame, attr_name):
        """Remove a specified item and adjust layout"""

        # Find corresponding attribute block
        attribute_block = None
        for block in self.attributes_frame.winfo_children():
            if isinstance(block, ctk.CTkFrame) and block.attribute_name == attr_name:
                attribute_block = block
                break

        if attribute_block is None:
            return

        # Confirm it's not removing the original item with a "+" sign
        for child in item_frame.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                for btn in child.winfo_children():
                    if isinstance(btn, ctk.CTkButton) and btn.cget("text") == "+":
                        msg = messagebox.showinfo("Info", "Cannot delete the original item with '+' sign", parent=self.window)
                        self.window.attributes('-topmost', 1)
                        msg.attributes('-topmost', 1)
                        self.window.after(200, lambda: [self.window.attributes('-topmost', 0), msg.attributes('-topmost', 0)])
                        return

        # Remove item
        item_frame.destroy()

        # Re-adjust remaining item row numbers
        current_row = 0
        for child in attribute_block.winfo_children():
            if isinstance(child, ctk.CTkFrame):
                if current_row == 0:  # Found attribute label
                    current_row += 1
                    continue
                ctk.CTkFrame.grid_configure(child, row=current_row)
                current_row += 1

    def _read_file_with_fallback_encoding(self, file_path):
        """File reading with encoding fallback, supports UTF-8, GBK(ANSI), and BOM"""
        encodings = ['utf-8-sig', 'utf-8', 'gbk', 'latin1']  # Add more encoding support

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                    # Check if the content contains invalid characters
                    if any(ord(char) > 127 and not char.isprintable() for char in content):
                        continue  # If it contains invalid characters, try the next encoding
                    return content.splitlines(), encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                raise

        # If all encoding attempts fail, try binary reading
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read()
                # Try UTF-8 decoding
                try:
                    return raw_data.decode('utf-8').splitlines(), 'utf-8'
                except UnicodeDecodeError:
                    # Try GBK decoding
                    try:
                        return raw_data.decode('gbk').splitlines(), 'gbk'
                    except UnicodeDecodeError:
                        # Finally try latin1 decoding
                        return raw_data.decode('latin1').splitlines(), 'latin1'
        except Exception as e:
            raise ValueError(f"Unrecognized file encoding: {file_path}")

    def rename_category(self, old_name):
        """Rename category (with centering functionality)"""
        new_name = None  # Initialize variable

        # Create dialog window
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("Rename Category")
        dialog.transient(self.window)
        dialog.grab_set()

        # Window content
        content_frame = ctk.CTkFrame(dialog)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Top tip
        ctk.CTkLabel(content_frame, text=f"Current Category: {old_name}", 
                    font=("Latin Modern Roman", 12)).pack(pady=(10, 5))

        # Input box
        input_frame = ctk.CTkFrame(content_frame)
        input_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(input_frame, text="New Name:", 
                    font=("Latin Modern Roman", 12)).pack(side="left", padx=5)
        name_var = tk.StringVar()
        name_entry = ctk.CTkEntry(input_frame, textvariable=name_var, width=150, font=("Latin Modern Roman", 12))
        name_entry.pack(side="left", padx=5)

        # Button area
        button_frame = ctk.CTkFrame(content_frame)
        button_frame.pack(fill="x", pady=(10, 5))

        def confirm_rename():
            nonlocal new_name  # Reference outer variable
            new_name = name_var.get().strip()
            if not new_name:
                messagebox.showwarning("Warning", "Category name cannot be empty", parent=self.window)
                return
            if new_name == old_name:
                dialog.destroy()
                return
            if os.path.exists(os.path.join(self.save_path, new_name)):
                messagebox.showerror("Error", "Category name already exists", parent=self.window)
                return

            try:
                os.rename(os.path.join(self.save_path, old_name),
                          os.path.join(self.save_path, new_name))
                self.load_categories()
                # Update category combobox
                self.category_combobox.configure(
                    values=self._get_all_categories())
                self.category_combobox.set(new_name)
                dialog.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"Rename failed: {str(e)}", parent=self.window)

        ctk.CTkButton(button_frame, text="Confirm",
                      command=confirm_rename, font=("Latin Modern Roman", 12)).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text="Cancel",
                      command=dialog.destroy, font=("Latin Modern Roman", 12)).pack(side="right", padx=10)

        # Center the window
        dialog.update_idletasks()
        d_width = dialog.winfo_width()
        d_height = dialog.winfo_height()
        x = self.window.winfo_x() + (self.window.winfo_width() - d_width) // 2
        y = self.window.winfo_y() + (self.window.winfo_height() - d_height) // 2
        dialog.geometry(f"+{x}+{y}")
        dialog.attributes('-topmost', 1)

    def on_close(self):
        """Close the window"""
        self.window.destroy()
