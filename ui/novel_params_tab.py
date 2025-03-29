# ui/novel_params_tab.py
# -*- coding: utf-8 -*- 
import customtkinter as ctk
from tkinter import filedialog, messagebox
from ui.context_menu import TextWidgetContextMenu
from tooltips import tooltips

def build_novel_params_area(self, start_row=1):
    self.params_frame = ctk.CTkScrollableFrame(self.right_frame, orientation="vertical")
    self.params_frame.grid(row=start_row, column=0, sticky="nsew", padx=5, pady=5)
    self.params_frame.columnconfigure(1, weight=1)

    # 1) Topic
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Topic:", tooltip_key="topic", row=0, column=0, font=("latin modern roman", 12), sticky="ne")
    self.topic_text = ctk.CTkTextbox(self.params_frame, height=80, wrap="word", font=("latin modern roman", 12))
    TextWidgetContextMenu(self.topic_text)
    self.topic_text.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
    if hasattr(self, 'topic_default') and self.topic_default:
        self.topic_text.insert("0.0", self.topic_default)

    # 2) Genre
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Genre:", tooltip_key="genre", row=1, column=0, font=("latin modern roman", 12))
    genre_entry = ctk.CTkEntry(self.params_frame, textvariable=self.genre_var, font=("latin modern roman", 12))
    genre_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

    # 3) Number of chapters & Word count per chapter
    row_for_chapter_and_word = 2
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Number of Chapters & Word Count per Chapter:", tooltip_key="num_chapters", row=row_for_chapter_and_word, column=0, font=("latin modern roman", 12))
    chapter_word_frame = ctk.CTkFrame(self.params_frame)
    chapter_word_frame.grid(row=row_for_chapter_and_word, column=1, padx=5, pady=5, sticky="ew")
    chapter_word_frame.columnconfigure((0, 1, 2, 3), weight=0)
    num_chapters_label = ctk.CTkLabel(chapter_word_frame, text="Number of Chapters:", font=("latin modern roman", 12))
    num_chapters_label.grid(row=0, column=0, padx=5, pady=5, sticky="e")
    num_chapters_entry = ctk.CTkEntry(chapter_word_frame, textvariable=self.num_chapters_var, width=60, font=("latin modern roman", 12))
    num_chapters_entry.grid(row=0, column=1, padx=5, pady=5, sticky="w")
    word_number_label = ctk.CTkLabel(chapter_word_frame, text="Word Count per Chapter:", font=("latin modern roman", 12))
    word_number_label.grid(row=0, column=2, padx=(15, 5), pady=5, sticky="e")
    word_number_entry = ctk.CTkEntry(chapter_word_frame, textvariable=self.word_number_var, width=60, font=("latin modern roman", 12))
    word_number_entry.grid(row=0, column=3, padx=5, pady=5, sticky="w")

    # 4) Save Path
    row_fp = 3
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Save Path:", tooltip_key="filepath", row=row_fp, column=0, font=("latin modern roman", 12))
    self.filepath_frame = ctk.CTkFrame(self.params_frame)
    self.filepath_frame.grid(row=row_fp, column=1, padx=5, pady=5, sticky="nsew")
    self.filepath_frame.columnconfigure(0, weight=1)
    filepath_entry = ctk.CTkEntry(self.filepath_frame, textvariable=self.filepath_var, font=("latin modern roman", 12))
    filepath_entry.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
    browse_btn = ctk.CTkButton(self.filepath_frame, text="Browse...", command=self.browse_folder, width=60, font=("latin modern roman", 12))
    browse_btn.grid(row=0, column=1, padx=5, pady=5, sticky="e")

    # 5) Chapter Number
    row_chap_num = 4
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Chapter Number:", tooltip_key="chapter_num", row=row_chap_num, column=0, font=("latin modern roman", 12))
    chapter_num_entry = ctk.CTkEntry(self.params_frame, textvariable=self.chapter_num_var, width=80, font=("latin modern roman", 12))
    chapter_num_entry.grid(row=row_chap_num, column=1, padx=5, pady=5, sticky="w")

    # 6) User Guidance
    row_user_guide = 5
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="User Guidance:", tooltip_key="user_guidance", row=row_user_guide, column=0, font=("latin modern roman", 12), sticky="ne")
    self.user_guide_text = ctk.CTkTextbox(self.params_frame, height=80, wrap="word", font=("latin modern roman", 12))
    TextWidgetContextMenu(self.user_guide_text)
    self.user_guide_text.grid(row=row_user_guide, column=1, padx=5, pady=5, sticky="nsew")
    if hasattr(self, 'user_guidance_default') and self.user_guidance_default:
        self.user_guide_text.insert("0.0", self.user_guidance_default)

    # 7) Optional Elements: Core Characters / Key Items / Scene Coordinates / Time Constraints
    row_idx = 6
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Core Characters:", tooltip_key="characters_involved", row=row_idx, column=0, font=("latin modern roman", 12))
    
    # Core Characters input box + button container
    char_inv_frame = ctk.CTkFrame(self.params_frame)
    char_inv_frame.grid(row=row_idx, column=1, padx=5, pady=5, sticky="nsew")
    char_inv_frame.columnconfigure(0, weight=1)
    char_inv_frame.rowconfigure(0, weight=1)
    
    # Three-line text input box
    self.char_inv_text = ctk.CTkTextbox(char_inv_frame, height=60, wrap="word", font=("latin modern roman", 12))
    self.char_inv_text.grid(row=0, column=0, padx=(0,5), pady=5, sticky="nsew")
    if hasattr(self, 'characters_involved_var'):
        self.char_inv_text.insert("0.0", self.characters_involved_var.get())
    
    # Import button
    import_btn = ctk.CTkButton(char_inv_frame, text="Import", width=60, 
                             command=self.show_character_import_window,
                             font=("latin modern roman", 12))
    import_btn.grid(row=0, column=1, padx=(0,5), pady=5, sticky="e")
    row_idx += 1
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Key Items:", tooltip_key="key_items", row=row_idx, column=0, font=("latin modern roman", 12))
    key_items_entry = ctk.CTkEntry(self.params_frame, textvariable=self.key_items_var, font=("latin modern roman", 12))
    key_items_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
    row_idx += 1
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Scene Coordinates:", tooltip_key="scene_location", row=row_idx, column=0, font=("latin modern roman", 12))
    scene_loc_entry = ctk.CTkEntry(self.params_frame, textvariable=self.scene_location_var, font=("latin modern roman", 12))
    scene_loc_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")
    row_idx += 1
    create_label_with_help_for_novel_params(self, parent=self.params_frame, label_text="Time Constraints:", tooltip_key="time_constraint", row=row_idx, column=0, font=("latin modern roman", 12))
    time_const_entry = ctk.CTkEntry(self.params_frame, textvariable=self.time_constraint_var, font=("latin modern roman", 12))
    time_const_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky="ew")

def build_optional_buttons_area(self, start_row=2):
    self.optional_btn_frame = ctk.CTkFrame(self.right_frame)
    self.optional_btn_frame.grid(row=start_row, column=0, sticky="ew", padx=5, pady=5)
    self.optional_btn_frame.columnconfigure((0, 1, 2, 3, 4), weight=1)

    self.btn_check_consistency = ctk.CTkButton(
        self.optional_btn_frame, text="Consistency Check", command=self.do_consistency_check, 
        font=("latin modern roman", 12), width=100  # Fixed width
    )
    self.btn_check_consistency.grid(row=0, column=0, padx=5, pady=5, sticky="ew")

    self.btn_import_knowledge = ctk.CTkButton(
        self.optional_btn_frame, text="Import Knowledge Base", command=self.import_knowledge_handler,
        font=("latin modern roman", 12), width=100
    )
    self.btn_import_knowledge.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

    self.btn_clear_vectorstore = ctk.CTkButton(
        self.optional_btn_frame, text="Clear Vectorstore", fg_color="red", 
        command=self.clear_vectorstore_handler, font=("latin modern roman", 12), width=100
    )
    self.btn_clear_vectorstore.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

    self.plot_arcs_btn = ctk.CTkButton(
        self.optional_btn_frame, text="View Plot Arcs", command=self.show_plot_arcs_ui,
        font=("latin modern roman", 12), width=100
    )
    self.plot_arcs_btn.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

    # Add role library button
    self.role_library_btn = ctk.CTkButton(
        self.optional_btn_frame, text="Role Library", command=self.show_role_library,
        font=("latin modern roman", 12), width=100
    )
    self.role_library_btn.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

def create_label_with_help_for_novel_params(self, parent, label_text, tooltip_key, row, column, font=None, sticky="e", padx=5, pady=5):
    frame = ctk.CTkFrame(parent)
    frame.grid(row=row, column=column, padx=padx, pady=pady, sticky=sticky)
    frame.columnconfigure(0, weight=0)
    label = ctk.CTkLabel(frame, text=label_text, font=font)
    label.pack(side="left")
    btn = ctk.CTkButton(frame, text="?", width=22, height=22, font=("latin modern roman", 10),
                        command=lambda: messagebox.showinfo("Parameter Description", tooltips.get(tooltip_key, "No description available")))
    btn.pack(side="left", padx=3)
    return frame
