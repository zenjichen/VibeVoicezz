import os
import sys

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import threading
import time
import queue
import json
import re
import hashlib
import subprocess
import unicodedata
import numpy as np
import torch
import soundfile as sf
import sounddevice as sd
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Set environment variable to bypass Windows symlink issue before loading HF hub
os.environ["HF_HUB_DISABLE_SYMLINKS"] = "1"

# Import OmniVoice components
try:
    from omnivoice import OmniVoice, OmniVoiceGenerationConfig
    from omnivoice.models.omnivoice import VoiceClonePrompt
    from omnivoice.utils.lang_map import LANG_NAMES, lang_display_name
except ImportError:
    messagebox.showerror(
        "Import Error",
        "Could not import OmniVoice. Please make sure you are running this script in the correct virtual environment."
    )
    sys.exit(1)

# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

APP_NAME = "OmniVoice Studio"
DEFAULT_MODEL_ID = "k2-fsa/OmniVoice"
REQUIRED_MODEL_IDS = (
    DEFAULT_MODEL_ID,
    "eustlb/higgs-audio-v2-tokenizer",
    "openai/whisper-large-v3-turbo",
)
TAB_CLONE = "Voice Clone"
TAB_DESIGN = "Voice Design"
TAB_LIBRARY = "Audio Library"

UI = {
    "page": ("#eef3f8", "#0b1020"),
    "panel": ("#ffffff", "#151b23"),
    "panel_soft": ("#f8fafc", "#1b2230"),
    "glass_hover": ("#e7edf5", "#252f3f"),
    "glass_active": ("#d9e9ff", "#183654"),
    "border": ("#d7e1ee", "#2b3546"),
    "border_hot": ("#8bbcff", "#58a6ff"),
    "text": ("#111827", "#f8fafc"),
    "muted": ("#5d6b7c", "#a9b4c3"),
    "accent": ("#2563eb", "#58a6ff"),
    "accent_hover": ("#1d4ed8", "#76b7ff"),
    "success": ("#0f9f6e", "#35d399"),
    "success_hover": ("#0b7f58", "#57e2ad"),
    "danger": ("#dc2626", "#ff6b6b"),
    "danger_hover": ("#b91c1c", "#ff8585"),
    "warning": ("#d97706", "#fbbf24"),
}

PULSE_COLORS = ["#58a6ff", "#7c3aed", "#06b6d4", "#35d399"]

# Available languages list
_ALL_LANGUAGES = ["Auto"] + sorted(lang_display_name(n) for n in LANG_NAMES)

# Voice Design categories
_CATEGORIES = {
    "Gender / Giới tính": ["Male / Nam", "Female / Nữ"],
    "Age / Tuổi tác": [
        "Child / Trẻ em",
        "Teenager / Thiếu niên",
        "Young Adult / Thanh niên",
        "Middle-aged / Trung niên",
        "Elderly / Người già",
    ],
    "Pitch / Cao độ": [
        "Very Low Pitch / Cực thấp",
        "Low Pitch / Thấp",
        "Moderate Pitch / Trung bình",
        "High Pitch / Cao",
        "Very High Pitch / Cực cao",
    ],
    "Style / Phong cách": ["Whisper / Thì thầm"],
    "English Accent / Giọng Tiếng Anh": [
        "American Accent / Giọng Mỹ",
        "Australian Accent / Giọng Úc",
        "British Accent / Giọng Anh",
        "Chinese Accent / Giọng Trung",
        "Canadian Accent / Giọng Canada",
        "Indian Accent / Giọng Ấn Độ",
        "Korean Accent / Giọng Hàn",
        "Portuguese Accent / Giọng Bồ Đào Nha",
        "Russian Accent / Giọng Nga",
        "Japanese Accent / Giọng Nhật",
    ],
    "Chinese Dialect / Phương ngữ Trung": [
        "Henan Dialect / Tiếng Hà Nam",
        "Shaanxi Dialect / Tiếng Thiểm Tây",
        "Sichuan Dialect / Tiếng Tứ Xuyên",
        "Guizhou Dialect / Tiếng Quý Châu",
        "Yunnan Dialect / Tiếng Vân Nam",
        "Guilin Dialect / Tiếng Quế Lâm",
        "Jinan Dialect / Tiếng Tế Nam",
        "Shijiazhuang Dialect / Tiếng Thạch Gia Trang",
        "Gansu Dialect / Tiếng Cam Túc",
        "Ningxia Dialect / Tiếng Ninh Hạ",
        "Qingdao Dialect / Tiếng Thanh Đảo",
        "Northeast Dialect / Tiếng Đông Bắc",
    ],
}


_CATEGORIES = {
    "Gender / Giới tính": ["Male / Nam", "Female / Nữ"],
    "Age / Tuổi tác": [
        "Child / Trẻ em",
        "Teenager / Thiếu niên",
        "Young Adult / Thanh niên",
        "Middle-aged / Trung niên",
        "Elderly / Người già",
    ],
    "Pitch / Cao độ": [
        "Very Low Pitch / Cực thấp",
        "Low Pitch / Thấp",
        "Moderate Pitch / Trung bình",
        "High Pitch / Cao",
        "Very High Pitch / Cực cao",
    ],
    "Style / Phong cách": ["Whisper / Thì thầm"],
    "English Accent / Giọng tiếng Anh": [
        "American Accent / Giọng Mỹ",
        "Australian Accent / Giọng Úc",
        "British Accent / Giọng Anh",
        "Chinese Accent / Giọng Trung",
        "Canadian Accent / Giọng Canada",
        "Indian Accent / Giọng Ấn Độ",
        "Korean Accent / Giọng Hàn",
        "Portuguese Accent / Giọng Bồ Đào Nha",
        "Russian Accent / Giọng Nga",
        "Japanese Accent / Giọng Nhật",
    ],
    "Chinese Dialect / Phương ngữ Trung": [
        "Henan Dialect / Tiếng Hà Nam",
        "Shaanxi Dialect / Tiếng Thiểm Tây",
        "Sichuan Dialect / Tiếng Tứ Xuyên",
        "Guizhou Dialect / Tiếng Quý Châu",
        "Yunnan Dialect / Tiếng Vân Nam",
        "Guilin Dialect / Tiếng Quế Lâm",
        "Jinan Dialect / Tiếng Tế Nam",
        "Shijiazhuang Dialect / Tiếng Thạch Gia Trang",
        "Gansu Dialect / Tiếng Cam Túc",
        "Ningxia Dialect / Tiếng Ninh Hạ",
        "Qingdao Dialect / Tiếng Thanh Đảo",
        "Northeast Dialect / Tiếng Đông Bắc",
    ],
}


class AudioPlayer:
    """Seekable audio player using sounddevice OutputStream."""
    def __init__(self):
        self.stream = None
        self.data = None
        self.samplerate = None
        self.current_frame = 0
        self.playing = False
        self.lock = threading.Lock()
        self.play_thread = None

    def load(self, data, samplerate):
        self.stop()
        with self.lock:
            # Normalize inputs
            if data.dtype == np.int16:
                self.data = data.astype(np.float32) / 32767.0
            else:
                self.data = data.astype(np.float32)
            
            # Ensure 1D mono or 2D channels
            if len(self.data.shape) > 2:
                self.data = self.data.squeeze()
            
            self.samplerate = samplerate
            self.current_frame = 0

    def play(self):
        if self.data is None:
            return
        if self.playing:
            return
        
        self.playing = True
        self.play_thread = threading.Thread(target=self._run, daemon=True)
        self.play_thread.start()

    def pause(self):
        self.playing = False

    def stop(self):
        self.playing = False
        if self.play_thread:
            self.play_thread.join(timeout=0.2)
        with self.lock:
            self.current_frame = 0

    def seek(self, position_seconds):
        if self.data is None:
            return
        with self.lock:
            target_frame = int(position_seconds * self.samplerate)
            self.current_frame = max(0, min(target_frame, len(self.data)))

    def get_duration(self):
        if self.data is None or self.samplerate is None:
            return 0
        return len(self.data) / self.samplerate

    def get_current_time(self):
        if self.data is None or self.samplerate is None:
            return 0
        return self.current_frame / self.samplerate

    def _run(self):
        blocksize = 1024
        channels = 1 if len(self.data.shape) == 1 else self.data.shape[1]
        
        def callback(outdata, frames, time_info, status):
            if not self.playing:
                raise sd.CallbackStop()
            
            with self.lock:
                remaining = len(self.data) - self.current_frame
                if remaining <= 0:
                    self.playing = False
                    raise sd.CallbackStop()
                
                chunk_size = min(frames, remaining)
                if channels == 1:
                    outdata[:chunk_size, 0] = self.data[self.current_frame:self.current_frame+chunk_size]
                else:
                    outdata[:chunk_size] = self.data[self.current_frame:self.current_frame+chunk_size]
                
                if chunk_size < frames:
                    outdata[chunk_size:] = 0
                
                self.current_frame += chunk_size

        try:
            with sd.OutputStream(samplerate=self.samplerate, channels=channels, blocksize=blocksize, callback=callback):
                while self.playing:
                    sd.sleep(50)
        except Exception as e:
            print("AudioPlayer stream error:", e)
            self.playing = False


class LanguageSelectorDialog(ctk.CTkToplevel):
    """Fast language picker using native tk.Listbox – renders 600+ items instantly."""
    def __init__(self, parent, current_selection="Auto", callback=None):
        super().__init__(parent)
        self.title("Select Language / Chọn ngôn ngữ")
        self.resizable(True, True)
        self.minsize(380, 480)

        # Center on parent
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        x = parent_x + (parent_w - 400) // 2
        y = parent_y + (parent_h - 520) // 2
        self.geometry(f"400x520+{x}+{y}")

        self.transient(parent)
        self.grab_set()
        self.lift()
        self.focus_force()

        self.callback = callback
        self.current_selection = current_selection
        self._all = _ALL_LANGUAGES

        # Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Search bar
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", self._on_search)
        search_entry = ctk.CTkEntry(
            self,
            placeholder_text="Gõ để tìm ngôn ngữ... / Type to search...",
            textvariable=self.search_var,
            height=36
        )
        search_entry.grid(row=0, column=0, padx=12, pady=(12, 6), sticky="ew")
        search_entry.focus()

        # Native tk.Listbox inside a CTkFrame wrapper – renders ALL items instantly
        import tkinter as tk
        list_frame = ctk.CTkFrame(self, corner_radius=8)
        list_frame.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self._listbox = tk.Listbox(
            list_frame,
            bg="#2b2b2b",
            fg="white",
            selectbackground="#1f538d",
            selectforeground="white",
            activestyle="none",
            bd=0,
            highlightthickness=0,
            relief="flat",
            font=("Segoe UI", 11),
            cursor="hand2"
        )
        scrollbar = tk.Scrollbar(list_frame, orient="vertical", command=self._listbox.yview)
        self._listbox.configure(yscrollcommand=scrollbar.set)
        self._listbox.grid(row=0, column=0, sticky="nsew", padx=(4, 0), pady=4)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=4)

        self._listbox.bind("<Double-Button-1>", self._on_double_click)
        self._listbox.bind("<Return>", self._on_double_click)

        # Populate immediately (native Listbox is blazing fast)
        self._populate(self._all)

        # Scroll to & select current item
        try:
            idx = self._all.index(self.current_selection)
            self._listbox.selection_set(idx)
            self._listbox.see(idx)
        except ValueError:
            pass

    def _populate(self, items):
        self._listbox.delete(0, "end")
        for lang in items:
            self._listbox.insert("end", lang)

    def _on_search(self, *args):
        query = self.search_var.get().lower().strip()
        if not query:
            filtered = self._all
        else:
            filtered = [l for l in self._all if query in l.lower()]
        self._populate(filtered)
        # Auto-select first result
        if filtered:
            self._listbox.selection_clear(0, "end")
            self._listbox.selection_set(0)
            self._listbox.see(0)

    def _on_double_click(self, event=None):
        sel = self._listbox.curselection()
        if sel:
            lang = self._listbox.get(sel[0])
            if self.callback:
                self.callback(lang)
            self.destroy()


class OmniVoiceGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"{APP_NAME} - Local Voice Tool")
        self.geometry("1180x850")
        self.minimum_size = (1040, 760)
        self.minsize(*self.minimum_size)
        self.configure(fg_color=UI["page"])

        # Base State variables
        self.model = None
        self.recording = False
        self.recorded_audio_path = os.path.join(os.getcwd(), "recorded_temp.wav")
        self.recorded_data = []
        self.recording_stream = None
        self.last_generated_audio = None  # Stores (sample_rate, numpy_array)
        self.last_generated_meta = {}
        self.last_saved_audio_path = ""
        self.log_queue = queue.Queue()

        # Custom Seekable Audio Player
        self.audio_player = AudioPlayer()
        self.play_state = "paused"
        self.user_dragging = False

        # Saved Presets management
        self.presets_file = os.path.join(os.getcwd(), "voice_presets.json")
        self.presets = self.load_presets()
        self.settings_file = os.path.join(os.getcwd(), "gui_settings.json")
        self.gui_settings = self.load_gui_settings()
        if "cache_voice_prompts" not in self.gui_settings:
            self.gui_settings["cache_voice_prompts"] = True
            self.save_gui_settings()
        self.last_saved_audio_path = self.gui_settings.get("last_save_file", "")
        self.loaded_model_name = ""

        # Library / History setup
        self.library_dir = os.path.join(os.getcwd(), "generated_audios")
        os.makedirs(self.library_dir, exist_ok=True)
        self.history_file = os.path.join(self.library_dir, "history.json")
        self.history = self.load_history()
        self.voice_prompt_cache_dir = os.path.join(os.getcwd(), "voice_prompt_cache")
        os.makedirs(self.voice_prompt_cache_dir, exist_ok=True)

        # Multi-select tracking for library
        self.selected_lib_ids = set()  # IDs of currently highlighted/selected items
        self.theme_mode = ctk.StringVar(value="Light")
        self._busy = False
        self._pulse_step = 0
        self._pulse_widgets = []

        # UI Layout setup
        self.setup_ui()
        self.update_open_path_button()
        self.initialize_model_entry()

        # Load initial presets into clone tab dropdown
        self.update_preset_dropdown()

        # Start background polling & loops
        self.after(100, self.poll_logs)
        self.after(100, self.update_player_ui)
        self.after(180, self.animate_activity)

    # --- Config and History I/O ---

    def panel(self, parent, **kwargs):
        """Create a soft glass-like panel that adapts to light/dark mode."""
        options = {
            "corner_radius": 18,
            "fg_color": UI["panel"],
            "border_width": 1,
            "border_color": UI["border"],
        }
        options.update(kwargs)
        return ctk.CTkFrame(parent, **options)

    def soft_panel(self, parent, **kwargs):
        options = {
            "corner_radius": 14,
            "fg_color": UI["panel_soft"],
            "border_width": 1,
            "border_color": UI["border"],
        }
        options.update(kwargs)
        return ctk.CTkFrame(parent, **options)

    def glass_button(self, parent, text, command=None, variant="neutral", **kwargs):
        styles = {
            "neutral": {
                "fg_color": "transparent",
                "hover_color": UI["glass_hover"],
                "border_color": UI["border"],
                "text_color": UI["text"],
            },
            "primary": {
                "fg_color": UI["glass_active"],
                "hover_color": UI["accent_hover"],
                "border_color": UI["border_hot"],
                "text_color": UI["text"],
            },
            "success": {
                "fg_color": "transparent",
                "hover_color": UI["success_hover"],
                "border_color": UI["success"],
                "text_color": UI["text"],
            },
            "danger": {
                "fg_color": "transparent",
                "hover_color": UI["danger_hover"],
                "border_color": UI["danger"],
                "text_color": UI["text"],
            },
        }
        options = {
            "text": text,
            "command": command,
            "height": 36,
            "corner_radius": 14,
            "border_width": 2,
            "font": ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        }
        options.update(styles.get(variant, styles["neutral"]))
        options.update(kwargs)
        return ctk.CTkButton(parent, **options)

    def styled_entry(self, parent, **kwargs):
        options = {
            "height": 36,
            "corner_radius": 12,
            "fg_color": UI["panel_soft"],
            "border_color": UI["border"],
            "text_color": UI["text"],
            "placeholder_text_color": UI["muted"],
        }
        options.update(kwargs)
        return ctk.CTkEntry(parent, **options)

    def styled_textbox(self, parent, **kwargs):
        options = {
            "corner_radius": 14,
            "fg_color": UI["panel_soft"],
            "border_color": UI["border"],
            "border_width": 1,
            "text_color": UI["text"],
        }
        options.update(kwargs)
        return ctk.CTkTextbox(parent, **options)

    def styled_combo(self, parent, **kwargs):
        options = {
            "height": 36,
            "corner_radius": 12,
            "fg_color": UI["panel_soft"],
            "border_color": UI["border"],
            "button_color": UI["glass_active"],
            "button_hover_color": UI["accent_hover"],
            "dropdown_fg_color": UI["panel"],
            "dropdown_hover_color": UI["glass_hover"],
            "text_color": UI["text"],
        }
        options.update(kwargs)
        return ctk.CTkComboBox(parent, **options)

    def load_gui_settings(self):
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                print("Error loading GUI settings:", e)
        return {}

    def save_gui_settings(self):
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.gui_settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error saving GUI settings: {e}")

    def remember_save_dir(self, file_path):
        file_path = os.path.abspath(file_path)
        save_dir = os.path.dirname(file_path)
        if save_dir:
            self.gui_settings["last_save_dir"] = save_dir
            self.gui_settings["last_save_file"] = file_path
            self.last_saved_audio_path = file_path
            self.save_gui_settings()
            self.update_open_path_button()

    def resolve_saved_file_path(self, file_path):
        if not file_path:
            return ""
        if os.path.isabs(file_path):
            return os.path.abspath(file_path)
        return os.path.abspath(os.path.join(os.getcwd(), file_path))

    def reveal_file_path(self, file_path, show_error=True):
        full_path = self.resolve_saved_file_path(file_path)
        if not full_path or not os.path.exists(full_path):
            if show_error:
                messagebox.showerror("Open Path", f"Không tìm thấy file:\n{full_path or file_path}")
            return False

        try:
            if sys.platform.startswith("win"):
                import ctypes

                params = f'/select,"{full_path}"'
                result = ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "open",
                    "explorer.exe",
                    params,
                    None,
                    1,
                )
                if result <= 32:
                    os.startfile(os.path.dirname(full_path))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", full_path])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(full_path)])
            self.log(f"Opened file location: {full_path}")
            return True
        except Exception as e:
            self.log(f"Error opening file location: {e}")
            if show_error:
                messagebox.showerror("Open Path", f"Không mở được nơi lưu file:\n{e}")
            return False

    def update_open_path_button(self):
        if not hasattr(self, "open_path_btn"):
            return
        path = getattr(self, "last_saved_audio_path", "") or self.gui_settings.get("last_save_file", "")
        state = "normal" if path and os.path.exists(self.resolve_saved_file_path(path)) else "disabled"
        self.open_path_btn.configure(state=state)

    def open_last_saved_audio_path(self):
        file_path = getattr(self, "last_saved_audio_path", "") or self.gui_settings.get("last_save_file", "")
        if not file_path:
            messagebox.showwarning("Open Path", "Chưa có file nào được lưu bằng nút Save Audio.")
            return
        self.reveal_file_path(file_path)

    def open_selected_library_audio_path(self):
        if not self.selected_lib_item:
            return
        self.reveal_file_path(self.selected_lib_item.get("file_path", ""))

    def show_saved_success(self, file_path):
        if hasattr(self, "status_label"):
            self.status_label.configure(text=f"Saved: {os.path.basename(file_path)}")
        messagebox.showinfo("Success", f"Successfully saved to:\n{file_path}")

    def smart_filename(self, mode=None, text=None):
        mode = (mode or self.last_generated_meta.get("mode") or "Audio").strip()
        text = (text if text is not None else self.last_generated_meta.get("text", "")).strip()
        snippet = "omnivoice"
        if text:
            normalized = unicodedata.normalize("NFKD", text)
            ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
            words = re.findall(r"[A-Za-z0-9]+", ascii_text.lower())
            if words:
                snippet = "_".join(words[:7])
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_mode = re.sub(r"[^A-Za-z0-9]+", "", mode.title()) or "Audio"
        filename = f"{safe_mode}_{snippet}_{timestamp}.wav"
        return filename[:120]

    def open_text_expander(self, title, textbox):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry("820x560")
        dialog.minsize(640, 420)
        dialog.configure(fg_color=UI["page"])
        dialog.transient(self)
        dialog.lift()
        dialog.focus_force()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        header = self.panel(dialog)
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=UI["text"],
        ).grid(row=0, column=0, padx=14, pady=(12, 2), sticky="w")
        ctk.CTkLabel(
            header,
            text="Soạn nội dung dài ở khung lớn, rồi bấm Thu nhỏ để đưa text về ô nhập chính.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=1, column=0, padx=14, pady=(0, 12), sticky="w")

        editor = self.styled_textbox(
            dialog,
            wrap="word",
            font=ctk.CTkFont(family="Segoe UI", size=14),
            border_width=2,
        )
        editor.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        editor.insert(ctk.END, textbox.get("1.0", ctk.END).strip())
        try:
            editor._textbox.configure(padx=16, pady=14, spacing3=6)
        except Exception:
            pass

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.grid(row=2, column=0, padx=16, pady=(4, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        counter = ctk.CTkLabel(
            footer,
            text="0 ký tự",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        )
        counter.grid(row=0, column=0, sticky="w")

        def update_counter(event=None):
            current = editor.get("1.0", ctk.END).strip()
            counter.configure(text=f"{len(current)} ký tự")

        def collapse():
            text = editor.get("1.0", ctk.END).strip()
            textbox.delete("1.0", ctk.END)
            textbox.insert(ctk.END, text)
            dialog.destroy()

        editor.bind("<KeyRelease>", update_counter)
        update_counter()

        self.glass_button(footer, text="Hủy", command=dialog.destroy, width=90).grid(row=0, column=1, padx=(0, 8), sticky="e")
        self.glass_button(footer, text="Thu nhỏ", command=collapse, width=120, variant="primary").grid(row=0, column=2, sticky="e")
        editor.focus()

    def set_busy(self, busy):
        self._busy = busy

    def animate_activity(self):
        """Subtle 3D-ish pulse while the app is loading or generating."""
        if self._busy and self._pulse_widgets:
            color = PULSE_COLORS[self._pulse_step % len(PULSE_COLORS)]
            for widget in self._pulse_widgets:
                try:
                    widget.configure(border_color=color)
                except Exception:
                    pass
            self._pulse_step += 1
        elif self._pulse_widgets:
            for widget in self._pulse_widgets:
                try:
                    widget.configure(border_color=UI["border"])
                except Exception:
                    pass
        self.after(180, self.animate_activity)

    def switch_theme(self, mode):
        self.theme_mode.set(mode)
        ctk.set_appearance_mode(mode)
        if hasattr(self, "log_textbox"):
            self.log(f"Theme switched to {mode}.")

    def find_local_model_dir(self, model_name):
        name = (model_name or DEFAULT_MODEL_ID).strip()
        expanded = os.path.abspath(os.path.expanduser(name))
        if os.path.isdir(expanded):
            return expanded

        repo_leaf = name.split("/")[-1].split("\\")[-1]
        candidates = [
            os.path.join(os.getcwd(), name),
            os.path.join(os.getcwd(), repo_leaf),
            os.path.join(os.getcwd(), "models", name),
            os.path.join(os.getcwd(), "models", repo_leaf),
            os.path.join(os.getcwd(), "models", name.replace("/", "--").replace("\\", "--")),
        ]
        for candidate in candidates:
            candidate = os.path.abspath(os.path.expanduser(candidate))
            if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, "config.json")):
                return candidate
        return ""

    def find_cached_model_dir(self, model_name):
        try:
            from huggingface_hub import snapshot_download

            return snapshot_download(model_name, local_files_only=True)
        except Exception:
            return ""

    def get_local_model_path(self, model_name):
        return self.find_local_model_dir(model_name) or self.find_cached_model_dir(model_name)

    def get_available_required_models(self):
        available = {}
        for model_id in REQUIRED_MODEL_IDS:
            local_path = self.get_local_model_path(model_id)
            if local_path:
                available[model_id] = local_path
        return available

    def initialize_model_entry(self):
        if not hasattr(self, "model_entry"):
            return

        available = self.get_available_required_models()
        has_default_model = DEFAULT_MODEL_ID in available
        self.model_entry.delete(0, ctk.END)

        if has_default_model:
            self.log("Local default model found. Model Path can be blank.")
            return

        self.model_entry.insert(0, DEFAULT_MODEL_ID)
        if not available:
            self.log("No local cache found for the 3 required models; default repo id was filled for download.")
        else:
            missing = ", ".join(model_id for model_id in REQUIRED_MODEL_IDS if model_id not in available)
            self.log(f"Default model is not local yet. Missing local model(s): {missing}")

    def warn_if_blank_model_needs_download(self, model_name):
        if model_name:
            return True

        available = self.get_available_required_models()
        if DEFAULT_MODEL_ID in available:
            return True

        self.model_entry.delete(0, ctk.END)
        self.model_entry.insert(0, DEFAULT_MODEL_ID)
        missing_lines = "\n".join(f"- {model_id}" for model_id in REQUIRED_MODEL_IDS if model_id not in available)
        if not missing_lines:
            missing_lines = f"- {DEFAULT_MODEL_ID}"

        return messagebox.askyesno(
            "Model local chưa có",
            "Ô Model Path đang trống nhưng local chưa có model mặc định.\n\n"
            "Các model chưa thấy trong local/cache:\n"
            f"{missing_lines}\n\n"
            f"Tiếp tục sẽ tải/dùng repo id: {DEFAULT_MODEL_ID}",
        )

    def resolve_model_checkpoint(self, model_name):
        requested = (model_name or "").strip() or DEFAULT_MODEL_ID

        local_dir = self.get_local_model_path(requested)
        if local_dir:
            self.log(f"Using local/cached model folder: {local_dir}")
            return local_dir, requested

        self.log(f"No local cache found for '{requested}'. Resolving from model path/repo id...")
        return requested, requested

    def set_voice_prompt_cache_enabled(self):
        if not hasattr(self, "clone_cache_prompt"):
            return
        self.gui_settings["cache_voice_prompts"] = bool(self.clone_cache_prompt.get())
        self.save_gui_settings()

    def get_voice_prompt_cache_key(self, ref_audio, ref_text, preprocess_prompt):
        full_path = os.path.abspath(os.path.expanduser(ref_audio))
        try:
            stat = os.stat(full_path)
            file_state = {
                "path": full_path,
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        except OSError:
            file_state = {"path": full_path, "size": None, "mtime_ns": None}

        payload = {
            "file": file_state,
            "ref_text": ref_text or "",
            "preprocess_prompt": bool(preprocess_prompt),
            "model": self.loaded_model_name or DEFAULT_MODEL_ID,
            "sampling_rate": getattr(self.model, "sampling_rate", None),
        }
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def get_voice_prompt_cache_path(self, ref_audio, ref_text, preprocess_prompt):
        cache_key = self.get_voice_prompt_cache_key(ref_audio, ref_text, preprocess_prompt)
        return os.path.join(self.voice_prompt_cache_dir, f"{cache_key}.pt")

    def load_voice_prompt_cache(self, ref_audio, ref_text, preprocess_prompt):
        if not self.gui_settings.get("cache_voice_prompts", True):
            return None

        cache_path = self.get_voice_prompt_cache_path(ref_audio, ref_text, preprocess_prompt)
        if not os.path.exists(cache_path):
            return None

        try:
            data = torch.load(cache_path, map_location="cpu")
            prompt = VoiceClonePrompt(
                ref_audio_tokens=data["ref_audio_tokens"],
                ref_text=data["ref_text"],
                ref_rms=float(data["ref_rms"]),
            )
            self.log(f"Using cached voice prompt: {os.path.basename(cache_path)}")
            return prompt
        except Exception as e:
            self.log(f"Voice prompt cache ignored: {e}")
            return None

    def save_voice_prompt_cache(self, ref_audio, ref_text, preprocess_prompt, prompt):
        if not self.gui_settings.get("cache_voice_prompts", True):
            return

        cache_path = self.get_voice_prompt_cache_path(ref_audio, ref_text, preprocess_prompt)
        try:
            torch.save(
                {
                    "ref_audio_tokens": prompt.ref_audio_tokens.detach().cpu(),
                    "ref_text": prompt.ref_text,
                    "ref_rms": prompt.ref_rms,
                },
                cache_path,
            )
            self.log(f"Saved voice prompt cache: {os.path.basename(cache_path)}")
        except Exception as e:
            self.log(f"Could not save voice prompt cache: {e}")

    def get_voice_clone_prompt(self, ref_audio, ref_text, preprocess_prompt):
        cached_prompt = self.load_voice_prompt_cache(ref_audio, ref_text, preprocess_prompt)
        if cached_prompt is not None:
            return cached_prompt

        self.log("Creating voice clone prompt from reference audio...")
        prompt = self.model.create_voice_clone_prompt(
            ref_audio=ref_audio,
            ref_text=ref_text if ref_text else None,
            preprocess_prompt=preprocess_prompt,
        )
        self.save_voice_prompt_cache(ref_audio, ref_text, preprocess_prompt, prompt)
        return prompt

    def read_text_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, "r", encoding="cp1258", errors="replace") as f:
                text = f.read()
        except Exception as e:
            return f"Khong doc duoc file {os.path.basename(path)}:\n{e}"

        if re.search(r"[ÃÂÆ][^\n]{0,8}|á»|Ä‘|Ä", text):
            try:
                repaired = text.encode("cp1252", errors="ignore").decode("utf-8", errors="ignore")
                if len(repaired) > len(text) * 0.55:
                    return repaired
            except Exception:
                pass
        return text

    def load_guide_text(self):
        for filename in ("HDSD_GUI_VN.md", "README.md"):
            path = os.path.join(os.getcwd(), filename)
            if os.path.exists(path):
                return self.clean_guide_text(self.read_text_file(path)), filename
        return "Khong tim thay README.md hoac HDSD_GUI_VN.md trong thu muc hien tai.", "N/A"

    def clean_guide_text(self, text):
        """Convert simple markdown into a cleaner in-app reading view."""
        text = re.sub(r"<[^>]+>", "", text)
        text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"^\s*-{3,}\s*$", "", text, flags=re.MULTILINE)
        text = re.sub(r"`([^`]+)`", r"\1", text)
        text = text.replace("**", "").replace("__", "").replace("*", "")

        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                if lines and lines[-1] != "":
                    lines.append("")
                continue

            heading = re.match(r"^(#{1,4})\s*(.+)$", line)
            if heading:
                title = heading.group(2).strip()
                if len(heading.group(1)) <= 2:
                    lines.append(title.upper())
                else:
                    lines.append(title)
                lines.append("")
                continue

            line = re.sub(r"^\s*[-+]\s+", "• ", line)
            line = re.sub(r"^\s*(\d+)\.\s+", r"\1. ", line)
            lines.append(line)

        cleaned = "\n".join(lines).strip()
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned

    def show_help_dialog_legacy(self):
        guide_text, source = self.load_guide_text()
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hướng dẫn sử dụng")
        dialog.geometry("780x620")
        dialog.minsize(620, 460)
        dialog.configure(fg_color=UI["page"])
        dialog.transient(self)
        dialog.lift()
        dialog.focus_force()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        header = self.panel(dialog)
        header.grid(row=0, column=0, padx=16, pady=(16, 8), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Hướng dẫn OmniVoice",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color=UI["text"],
        ).grid(row=0, column=0, padx=16, pady=(12, 2), sticky="w")
        ctk.CTkLabel(
            header,
            text=f"Nguồn: {source}",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=1, column=0, padx=16, pady=(0, 12), sticky="w")

        textbox = self.styled_textbox(dialog, wrap="word")
        textbox.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        textbox.insert(ctk.END, guide_text.strip())
        textbox.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.grid(row=2, column=0, padx=16, pady=(4, 16), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        self.glass_button(
            footer,
            text="? Mở README",
            command=lambda: os.startfile(os.path.join(os.getcwd(), "README.md")) if os.path.exists(os.path.join(os.getcwd(), "README.md")) else None,
            width=140,
        ).grid(row=0, column=0, sticky="w")
        self.glass_button(footer, text="Đóng", command=dialog.destroy, width=100).grid(row=0, column=1, sticky="e")

    def show_help_dialog_text_legacy(self):
        guide_text, source = self.load_guide_text()
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hướng dẫn sử dụng")
        dialog.geometry("860x660")
        dialog.minsize(700, 520)
        dialog.configure(fg_color=UI["page"])
        dialog.transient(self)
        dialog.lift()
        dialog.focus_force()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        header = self.panel(dialog)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkFrame(
            header,
            width=44,
            height=44,
            corner_radius=14,
            fg_color=UI["glass_active"],
            border_width=2,
            border_color=UI["border_hot"],
        )
        icon.grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=12)
        icon.grid_propagate(False)
        ctk.CTkLabel(
            icon,
            text="?",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=UI["text"],
        ).place(relx=0.5, rely=0.48, anchor="center")

        ctk.CTkLabel(
            header,
            text="Hướng dẫn OmniVoice",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=UI["text"],
        ).grid(row=0, column=1, padx=0, pady=(13, 2), sticky="w")
        ctk.CTkLabel(
            header,
            text="Các bước sử dụng nhanh, đã lọc định dạng markdown để dễ đọc trong app.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=1, column=1, padx=0, pady=(0, 13), sticky="w")

        source_badge = self.glass_button(
            header,
            text=f"Nguồn: {source}",
            width=150,
            height=32,
            state="disabled",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
        )
        source_badge.grid(row=0, column=2, rowspan=2, padx=14, pady=12, sticky="e")

        textbox = self.styled_textbox(
            dialog,
            wrap="word",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            border_width=2,
        )
        textbox.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="nsew")
        textbox.insert(ctk.END, guide_text.strip())
        try:
            textbox._textbox.configure(spacing1=3, spacing3=7, padx=18, pady=16)
        except Exception:
            pass
        textbox.configure(state="disabled")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        self.glass_button(
            footer,
            text="Mở README",
            command=lambda: os.startfile(os.path.join(os.getcwd(), "README.md")) if os.path.exists(os.path.join(os.getcwd(), "README.md")) else None,
            width=130,
            height=38,
        ).grid(row=0, column=0, sticky="w")
        self.glass_button(
            footer,
            text="Đóng",
            command=dialog.destroy,
            width=110,
            height=38,
            variant="primary",
        ).grid(row=0, column=1, sticky="e")

    def show_help_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Hướng dẫn sử dụng")
        dialog.geometry("880x660")
        dialog.minsize(760, 540)
        dialog.configure(fg_color=UI["page"])
        dialog.transient(self)
        dialog.lift()
        dialog.focus_force()

        dialog.grid_columnconfigure(0, weight=1)
        dialog.grid_rowconfigure(1, weight=1)

        header = self.panel(dialog)
        header.grid(row=0, column=0, padx=18, pady=(18, 10), sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        icon = ctk.CTkFrame(
            header,
            width=44,
            height=44,
            corner_radius=14,
            fg_color=UI["glass_active"],
            border_width=2,
            border_color=UI["border_hot"],
        )
        icon.grid(row=0, column=0, rowspan=2, padx=(14, 12), pady=12)
        icon.grid_propagate(False)
        ctk.CTkLabel(
            icon,
            text="?",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=UI["text"],
        ).place(relx=0.5, rely=0.48, anchor="center")

        ctk.CTkLabel(
            header,
            text="Hướng dẫn nhanh OmniVoice",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=UI["text"],
        ).grid(row=0, column=1, padx=0, pady=(13, 2), sticky="w")
        ctk.CTkLabel(
            header,
            text="Tóm tắt các thao tác quan trọng. README vẫn có thể mở để xem bản đầy đủ.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=1, column=1, padx=0, pady=(0, 13), sticky="w")

        self.glass_button(
            header,
            text="Mở README",
            command=lambda: os.startfile(os.path.join(os.getcwd(), "README.md")) if os.path.exists(os.path.join(os.getcwd(), "README.md")) else None,
            width=120,
            height=36,
        ).grid(row=0, column=2, rowspan=2, padx=14, pady=12, sticky="e")

        content = ctk.CTkScrollableFrame(
            dialog,
            corner_radius=16,
            fg_color=UI["panel"],
            border_width=1,
            border_color=UI["border"],
        )
        content.grid(row=1, column=0, padx=18, pady=(0, 10), sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        guide_cards = [
            (
                "Bắt đầu",
                "Nạp model trước khi tạo giọng.",
                ["Chọn device: cuda nếu có GPU, cpu nếu chạy phổ thông.", "Giữ model mặc định k2-fsa/OmniVoice nếu không cần repo khác."],
                UI["accent"],
            ),
            (
                "Voice Clone",
                "Clone giọng từ file mẫu hoặc micro.",
                ["Chọn audio mẫu 3-10 giây, càng sạch càng tốt.", "Nhập Reference Text nếu biết nội dung file mẫu.", "Bấm Generate Voice Clone trong khung Settings."],
                UI["success"],
            ),
            (
                "Voice Design",
                "Tạo giọng theo thuộc tính.",
                ["Chọn giới tính, tuổi, cao độ hoặc accent.", "Để Auto ở mục chưa chắc chắn.", "Tối ưu nhất với tiếng Anh và tiếng Trung."],
                UI["warning"],
            ),
            (
                "Audio Library",
                "Quản lý các file đã tạo.",
                ["Click một audio để xem chi tiết.", "Ctrl + Click để chọn nhiều file.", "Load & Play để nghe lại trong player bên dưới."],
                UI["accent_hover"],
            ),
            (
                "Generation Settings",
                "Tinh chỉnh chất lượng và tốc độ.",
                ["Steps cao hơn cho âm thanh chi tiết hơn nhưng chậm hơn.", "CFG cao giúp bám prompt hơn, quá cao có thể méo tiếng.", "Fixed Duration dùng khi cần khớp thời lượng video."],
                UI["danger"],
            ),
            (
                "Media Player",
                "Nghe và lưu file nhanh.",
                ["Play/Pause để kiểm tra kết quả.", "Kéo slider để tua.", "Save Audio để xuất WAV ra vị trí bạn chọn."],
                UI["success_hover"],
            ),
        ]

        for index, (title, summary, bullets, accent) in enumerate(guide_cards):
            card = self.soft_panel(content, border_width=2, border_color=accent)
            card.grid(row=index // 2, column=index % 2, padx=10, pady=10, sticky="nsew")
            card.grid_columnconfigure(0, weight=1)

            ctk.CTkLabel(
                card,
                text=title,
                font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"),
                text_color=accent,
                anchor="w",
            ).grid(row=0, column=0, padx=14, pady=(12, 2), sticky="ew")
            ctk.CTkLabel(
                card,
                text=summary,
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color=UI["text"],
                anchor="w",
                wraplength=330,
            ).grid(row=1, column=0, padx=14, pady=(0, 8), sticky="ew")

            for bullet_index, bullet in enumerate(bullets, start=2):
                ctk.CTkLabel(
                    card,
                    text=f"• {bullet}",
                    font=ctk.CTkFont(family="Segoe UI", size=12),
                    text_color=UI["muted"],
                    anchor="w",
                    justify="left",
                    wraplength=340,
                ).grid(row=bullet_index, column=0, padx=14, pady=(0, 5), sticky="ew")

        footer = ctk.CTkFrame(dialog, fg_color="transparent")
        footer.grid(row=2, column=0, padx=18, pady=(0, 18), sticky="ew")
        footer.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            footer,
            text="Mẹo: sau khi tạo xong, audio tự lưu vào Audio Library.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=0, column=0, sticky="w")
        self.glass_button(
            footer,
            text="Đóng",
            command=dialog.destroy,
            width=110,
            height=38,
            variant="primary",
        ).grid(row=0, column=1, sticky="e")

    def load_presets(self):
        if os.path.exists(self.presets_file):
            try:
                with open(self.presets_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading presets:", e)
        return {}

    def save_presets_to_file(self):
        try:
            with open(self.presets_file, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error saving presets: {e}")

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print("Error loading library history:", e)
        return []

    def save_history_to_file(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error saving library history: {e}")

    # --- Background Loops ---

    def log(self, message):
        self.log_queue.put(message)

    def poll_logs(self):
        try:
            while True:
                msg = self.log_queue.get_nowait()
                self.log_textbox.insert(ctk.END, f"{msg}\n")
                self.log_textbox.see(ctk.END)
        except queue.Empty:
            pass
        self.after(100, self.poll_logs)

    def update_player_ui(self):
        """Update playback slider and time labels periodically."""
        if self.audio_player.playing:
            duration = self.audio_player.get_duration()
            current = self.audio_player.get_current_time()
            if duration > 0 and not self.user_dragging:
                self.player_slider.set(current / duration)
                self.time_label.configure(text=f"{self.format_time(current)} / {self.format_time(duration)}")
        else:
            # Handle end of track naturally
            if self.play_state == "playing" and not self.audio_player.playing:
                self.play_state = "paused"
                self.play_btn.configure(text="Play")
                self.player_slider.set(1.0)
                duration = self.audio_player.get_duration()
                self.time_label.configure(text=f"{self.format_time(duration)} / {self.format_time(duration)}")

        self.after(100, self.update_player_ui)

    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02d}:{secs:02d}"

    # --- UI Builders ---

    def setup_ui_legacy(self):
        # Configure root layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Top Panel: Model Loader ---
        self.model_frame = ctk.CTkFrame(self, corner_radius=10)
        self.model_frame.grid(row=0, column=0, padx=15, pady=10, sticky="nsew")
        self.model_frame.grid_columnconfigure(1, weight=1)

        model_label = ctk.CTkLabel(self.model_frame, text="Model Path / Repo ID:", font=ctk.CTkFont(weight="bold"))
        model_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.model_entry = ctk.CTkEntry(self.model_frame, placeholder_text=f"{DEFAULT_MODEL_ID} (blank = local cache/default)")
        self.model_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        device_label = ctk.CTkLabel(self.model_frame, text="Device:")
        device_label.grid(row=0, column=2, padx=5, pady=10, sticky="e")

        self.device_combo = ctk.CTkComboBox(self.model_frame, values=["cuda", "cpu", "mps"], width=100)
        if torch.cuda.is_available():
            self.device_combo.set("cuda")
        elif torch.backends.mps.is_available():
            self.device_combo.set("mps")
        else:
            self.device_combo.set("cpu")
        self.device_combo.grid(row=0, column=3, padx=5, pady=10, sticky="e")

        self.load_model_btn = ctk.CTkButton(self.model_frame, text="Load Model", command=self.start_load_model, fg_color="#1f538d")
        self.load_model_btn.grid(row=0, column=4, padx=10, pady=10, sticky="e")

        # --- Middle Panel: Tabview ---
        self.tabview = ctk.CTkTabview(self, corner_radius=10)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")

        self.clone_tab = self.tabview.add("Voice Clone (Clone giọng nói)")
        self.design_tab = self.tabview.add("Voice Design (Tạo giọng theo thuộc tính)")
        self.library_tab = self.tabview.add("Audio Library (Thư viện Audio)")

        self.setup_clone_tab()
        self.setup_design_tab()
        self.setup_library_tab()

        # --- Bottom Panel: Unified Seekable Player & Logs ---
        self.bottom_frame = ctk.CTkFrame(self, corner_radius=10)
        self.bottom_frame.grid(row=2, column=0, padx=15, pady=10, sticky="nsew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        # Media Player Control Row
        self.player_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.player_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.player_frame.grid_columnconfigure(2, weight=1)

        self.status_label = ctk.CTkLabel(self.player_frame, text="Status: Ready", font=ctk.CTkFont(weight="bold"), width=180, anchor="w")
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.play_btn = ctk.CTkButton(
            self.player_frame, 
            text="▶ Play", 
            command=self.toggle_play_pause, 
            state="disabled", 
            fg_color="#2eb872", 
            hover_color="#1b824c", 
            width=100
        )
        self.play_btn.grid(row=0, column=1, padx=5, pady=5)

        # Seek Slider
        self.player_slider = ctk.CTkSlider(self.player_frame, from_=0.0, to=1.0, command=self.on_slider_drag)
        self.player_slider.set(0.0)
        self.player_slider.grid(row=0, column=2, padx=10, pady=5, sticky="ew")
        
        # Binding mouse drag events to lock updates
        self.player_slider.bind("<ButtonPress-1>", lambda e: setattr(self, "user_dragging", True))
        self.player_slider.bind("<ButtonRelease-1>", lambda e: setattr(self, "user_dragging", False))

        # Time code
        self.time_label = ctk.CTkLabel(self.player_frame, text="00:00 / 00:00", font=ctk.CTkFont(family="Courier"))
        self.time_label.grid(row=0, column=3, padx=10, pady=5)

        self.save_btn = ctk.CTkButton(self.player_frame, text="Save Audio / Lưu file", command=self.save_audio, state="disabled", fg_color="#4f5b66", hover_color="#343d46", width=140)
        self.save_btn.grid(row=0, column=4, padx=10, pady=5)

        self.open_path_btn = ctk.CTkButton(self.player_frame, text="Open Path", command=self.open_last_saved_audio_path, state="disabled", fg_color="#4f5b66", hover_color="#343d46", width=110)
        self.open_path_btn.grid(row=0, column=5, padx=(0, 10), pady=5)

        # Log Terminal
        self.log_textbox = ctk.CTkTextbox(self.bottom_frame, height=100)
        self.log_textbox.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        self.log_textbox.insert(ctk.END, "=== OmniVoice GUI Local Console ===\n")

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.header_frame = self.panel(self)
        self.header_frame.grid(row=0, column=0, padx=16, pady=(10, 6), sticky="ew")
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.brand_mark = ctk.CTkFrame(
            self.header_frame,
            width=46,
            height=46,
            corner_radius=16,
            fg_color=UI["glass_active"],
            border_width=1,
            border_color=UI["border_hot"],
        )
        self.brand_mark.grid(row=0, column=0, padx=(14, 10), pady=8)
        self.brand_mark.grid_propagate(False)
        ctk.CTkLabel(
            self.brand_mark,
            text="OV",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            text_color=UI["text"],
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_box = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        title_box.grid(row=0, column=1, padx=0, pady=8, sticky="ew")
        ctk.CTkLabel(
            title_box,
            text=APP_NAME,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=UI["text"],
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            title_box,
            text="Local voice clone, design, library and playback workspace",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=UI["muted"],
        ).grid(row=1, column=0, sticky="w")

        self.theme_switch = ctk.CTkSegmentedButton(
            self.header_frame,
            values=["Light", "Dark"],
            variable=self.theme_mode,
            command=self.switch_theme,
            corner_radius=14,
            selected_color=UI["glass_active"],
            selected_hover_color=UI["accent_hover"],
            unselected_color=UI["panel_soft"],
            unselected_hover_color=UI["glass_hover"],
            border_width=1,
            fg_color=UI["panel_soft"],
            text_color=UI["text"],
        )
        self.theme_switch.grid(row=0, column=2, padx=(10, 8), pady=8, sticky="e")
        self.theme_switch.set("Light")

        self.help_btn = self.glass_button(self.header_frame, text="? Hướng dẫn", command=self.show_help_dialog, width=116)
        self.help_btn.grid(row=0, column=3, padx=(0, 14), pady=8, sticky="e")
        self.header_frame.grid_remove()

        self.model_frame = self.panel(self)
        self.model_frame.grid(row=0, column=0, padx=16, pady=(10, 6), sticky="nsew")
        self.model_frame.grid_columnconfigure(1, weight=1)
        self._pulse_widgets = [self.model_frame]

        model_label = ctk.CTkLabel(
            self.model_frame,
            text="Model Path / Repo ID",
            font=ctk.CTkFont(family="Segoe UI", weight="bold"),
            text_color=UI["text"],
        )
        model_label.grid(row=0, column=0, padx=(14, 8), pady=8, sticky="w")

        self.model_entry = self.styled_entry(self.model_frame, placeholder_text=f"{DEFAULT_MODEL_ID} (blank = local cache/default)")
        self.model_entry.grid(row=0, column=1, padx=8, pady=8, sticky="ew")

        device_label = ctk.CTkLabel(self.model_frame, text="Device", text_color=UI["muted"])
        device_label.grid(row=0, column=2, padx=5, pady=10, sticky="e")

        self.device_combo = self.styled_combo(self.model_frame, values=["cuda", "cpu", "mps"], width=100)
        if torch.cuda.is_available():
            self.device_combo.set("cuda")
        elif torch.backends.mps.is_available():
            self.device_combo.set("mps")
        else:
            self.device_combo.set("cpu")
        self.device_combo.grid(row=0, column=3, padx=5, pady=10, sticky="e")

        self.load_model_btn = self.glass_button(self.model_frame, text="Load Model", command=self.start_load_model, variant="primary", width=120)
        self.load_model_btn.grid(row=0, column=4, padx=(8, 14), pady=8, sticky="e")

        self.theme_switch = ctk.CTkSegmentedButton(
            self.model_frame,
            values=["Light", "Dark"],
            variable=self.theme_mode,
            command=self.switch_theme,
            corner_radius=14,
            selected_color=UI["glass_active"],
            selected_hover_color=UI["accent_hover"],
            unselected_color=UI["panel_soft"],
            unselected_hover_color=UI["glass_hover"],
            border_width=1,
            fg_color=UI["panel_soft"],
            text_color=UI["text"],
        )
        self.theme_switch.grid(row=0, column=5, padx=(0, 8), pady=8, sticky="e")
        self.theme_switch.set("Light")

        self.help_btn = self.glass_button(self.model_frame, text="? Hướng dẫn", command=self.show_help_dialog, width=116)
        self.help_btn.grid(row=0, column=6, padx=(0, 14), pady=8, sticky="e")

        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=18,
            fg_color=UI["panel"],
            border_width=1,
            border_color=UI["border"],
            segmented_button_fg_color=UI["panel_soft"],
            segmented_button_selected_color=UI["glass_active"],
            segmented_button_selected_hover_color=UI["accent_hover"],
            segmented_button_unselected_color=UI["panel_soft"],
            segmented_button_unselected_hover_color=UI["glass_hover"],
            text_color=UI["text"],
        )
        self.tabview.grid(row=1, column=0, padx=16, pady=8, sticky="nsew")
        self.tabview._segmented_button.configure(
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=36,
        )

        self.clone_tab = self.tabview.add(TAB_CLONE)
        self.design_tab = self.tabview.add(TAB_DESIGN)
        self.library_tab = self.tabview.add(TAB_LIBRARY)

        self.setup_clone_tab()
        self.setup_design_tab()
        self.setup_library_tab()

        self.bottom_frame = self.panel(self)
        self.bottom_frame.grid(row=2, column=0, padx=16, pady=(4, 10), sticky="nsew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.player_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.player_frame.grid(row=0, column=0, padx=12, pady=(10, 4), sticky="ew")
        self.player_frame.grid_columnconfigure(3, weight=1)

        self.status_label = ctk.CTkLabel(
            self.player_frame,
            text="Status: Ready",
            font=ctk.CTkFont(family="Segoe UI", weight="bold"),
            text_color=UI["text"],
            width=180,
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        self.play_btn = self.glass_button(
            self.player_frame,
            text="Play",
            command=self.toggle_play_pause,
            state="disabled",
            variant="success",
            width=112,
            height=40,
            corner_radius=16,
            border_width=2,
            fg_color=UI["panel_soft"],
        )
        self.play_btn.grid(row=0, column=1, padx=5, pady=5)

        self.replay_btn = self.glass_button(
            self.player_frame,
            text="Replay Voice",
            command=self.replay_audio,
            state="disabled",
            width=128,
            height=40,
            corner_radius=16,
            border_width=2,
        )
        self.replay_btn.grid(row=0, column=2, padx=5, pady=5)

        self.player_slider = ctk.CTkSlider(
            self.player_frame,
            from_=0.0,
            to=1.0,
            command=self.on_slider_drag,
            button_color=UI["accent"],
            button_hover_color=UI["accent_hover"],
            progress_color=UI["accent"],
            fg_color=UI["panel_soft"],
        )
        self.player_slider.set(0.0)
        self.player_slider.grid(row=0, column=3, padx=10, pady=5, sticky="ew")
        self.player_slider.bind("<ButtonPress-1>", lambda e: setattr(self, "user_dragging", True))
        self.player_slider.bind("<ButtonRelease-1>", lambda e: setattr(self, "user_dragging", False))

        self.time_label = ctk.CTkLabel(
            self.player_frame,
            text="00:00 / 00:00",
            font=ctk.CTkFont(family="Consolas", size=12),
            text_color=UI["muted"],
        )
        self.time_label.grid(row=0, column=4, padx=10, pady=5)

        self.save_btn = self.glass_button(self.player_frame, text="Save Audio", command=self.save_audio, state="disabled", width=130)
        self.save_btn.grid(row=0, column=5, padx=10, pady=5)

        self.open_path_btn = self.glass_button(
            self.player_frame,
            text="Open Path",
            command=self.open_last_saved_audio_path,
            state="disabled",
            width=110,
        )
        self.open_path_btn.grid(row=0, column=6, padx=(0, 10), pady=5)

        self.log_textbox = self.styled_textbox(self.bottom_frame, height=72)
        self.log_textbox.grid(row=1, column=0, padx=12, pady=(4, 12), sticky="ew")
        self.log_textbox.insert(ctk.END, "=== OmniVoice Studio Console ===\n")

    def setup_clone_tab(self):
        self.clone_tab.grid_columnconfigure(0, weight=1)
        self.clone_tab.grid_columnconfigure(1, weight=1)

        # Left Column - Inputs
        left_col = ctk.CTkFrame(self.clone_tab, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_col.grid_columnconfigure(1, weight=1)

        # --- Preset Voice Config Manager Frame ---
        preset_frame = self.soft_panel(left_col)
        preset_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10), padx=2)
        preset_frame.grid_columnconfigure(1, weight=1)

        pr_label = ctk.CTkLabel(preset_frame, text="Mẫu giọng đã lưu:", font=ctk.CTkFont(weight="bold"))
        pr_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

        self.preset_combo = self.styled_combo(preset_frame, values=["-- Select Preset --"], command=self.on_preset_selected)
        self.preset_combo.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        preset_btn_row = ctk.CTkFrame(preset_frame, fg_color="transparent")
        preset_btn_row.grid(row=0, column=2, padx=10, pady=10, sticky="e")

        self.save_preset_btn = self.glass_button(preset_btn_row, text="Save", command=self.save_current_preset, variant="success", width=80)
        self.save_preset_btn.pack(side="left", padx=2)

        self.del_preset_btn = self.glass_button(preset_btn_row, text="Delete", command=self.delete_selected_preset, variant="danger", width=80)
        self.del_preset_btn.pack(side="left", padx=2)

        # Text to synthesize
        txt_label = ctk.CTkLabel(left_col, text="Text to Synthesize / Văn bản cần đọc:")
        txt_label.grid(row=1, column=0, sticky="w", pady=(0, 2))
        self.clone_expand_btn = self.glass_button(
            left_col,
            text="Mở rộng",
            width=96,
            height=30,
            command=lambda: self.open_text_expander("Mở rộng text Voice Clone", self.clone_text),
        )
        self.clone_expand_btn.grid(row=1, column=1, sticky="e", pady=(0, 2))
        self.clone_text = self.styled_textbox(left_col, height=120)
        self.clone_text.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.clone_text.insert(ctk.END, "Xin chào, đây là giọng nói đã được clone trực tiếp bằng ứng dụng OmniVoice local của tôi.")

        # Reference Audio selector
        ref_label = ctk.CTkLabel(left_col, text="Reference Audio / Giọng nói mẫu:")
        ref_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 2))

        self.ref_audio_entry = self.styled_entry(left_col, placeholder_text="Đường dẫn file .wav mẫu hoặc dùng nút Ghi âm")
        self.ref_audio_entry.grid(row=4, column=0, sticky="ew", padx=(0, 5))

        btn_row = ctk.CTkFrame(left_col, fg_color="transparent")
        btn_row.grid(row=4, column=1, sticky="w")
        
        self.browse_btn = self.glass_button(btn_row, text="Browse", width=82, command=self.browse_ref_audio)
        self.browse_btn.pack(side="left", padx=2)

        self.record_btn = self.glass_button(btn_row, text="Record", variant="danger", width=90, command=self.toggle_recording)
        self.record_btn.pack(side="left", padx=2)

        # Reference text (optional)
        ref_txt_label = ctk.CTkLabel(left_col, text="Reference Text (optional) / Văn bản của giọng mẫu (Tùy chọn):")
        ref_txt_label.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.clone_ref_text = self.styled_entry(left_col, placeholder_text="Nhập nội dung giọng nói mẫu nếu có để clone chuẩn hơn...")
        self.clone_ref_text.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Language selection
        lang_label = ctk.CTkLabel(left_col, text="Language / Ngôn ngữ:")
        lang_label.grid(row=7, column=0, sticky="w", pady=(5, 2))
        
        self.clone_lang = "Auto"
        lang_btn_row = ctk.CTkFrame(left_col, fg_color="transparent")
        lang_btn_row.grid(row=7, column=1, sticky="ew", pady=(5, 2))
        lang_btn_row.grid_columnconfigure(0, weight=1)
        
        self.clone_lang_lbl = ctk.CTkLabel(lang_btn_row, text="Auto", font=ctk.CTkFont(weight="bold"), anchor="w")
        self.clone_lang_lbl.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.clone_lang_btn = self.glass_button(lang_btn_row, text="Select", width=100, command=self.choose_clone_lang)
        self.clone_lang_btn.grid(row=0, column=1, sticky="e")

        # Right Column - Parameters Settings
        right_col = self.soft_panel(self.clone_tab)
        right_col.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_col.grid_columnconfigure(1, weight=1)

        settings_title = ctk.CTkLabel(right_col, text="Generation Settings", font=ctk.CTkFont(weight="bold", size=14))
        settings_title.grid(row=0, column=0, columnspan=2, pady=10)

        # Inference Steps
        steps_lbl = ctk.CTkLabel(right_col, text="Inference Steps (Mặc định: 32):")
        steps_lbl.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.clone_steps = ctk.CTkSlider(right_col, from_=4, to=64, number_of_steps=60)
        self.clone_steps.set(32)
        self.clone_steps.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Guidance Scale
        cfg_lbl = ctk.CTkLabel(right_col, text="Guidance Scale (CFG):")
        cfg_lbl.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.clone_cfg = ctk.CTkSlider(right_col, from_=0.0, to=4.0, number_of_steps=40)
        self.clone_cfg.set(2.0)
        self.clone_cfg.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Speed
        speed_lbl = ctk.CTkLabel(right_col, text="Speed Factor (Tốc độ):")
        speed_lbl.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.clone_speed = ctk.CTkSlider(right_col, from_=0.5, to=1.5, number_of_steps=20)
        self.clone_speed.set(1.0)
        self.clone_speed.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Duration
        dur_lbl = ctk.CTkLabel(right_col, text="Fixed Duration (s):")
        dur_lbl.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.clone_duration = self.styled_entry(right_col, placeholder_text="Trống (Tính theo speed)")
        self.clone_duration.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # Checkboxes
        self.clone_denoise = ctk.CTkCheckBox(right_col, text="Denoise Audio (Lọc nhiễu)")
        self.clone_denoise.select()
        self.clone_denoise.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.clone_preprocess = ctk.CTkCheckBox(right_col, text="Preprocess Prompt (Lọc và cắt khoảng lặng file mẫu)")
        self.clone_preprocess.select()
        self.clone_preprocess.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.clone_postprocess = ctk.CTkCheckBox(right_col, text="Postprocess Output (Cắt khoảng lặng file kết quả)")
        self.clone_postprocess.select()
        self.clone_postprocess.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.clone_cache_prompt = ctk.CTkCheckBox(
            right_col,
            text="Cache Voice Prompt (reuse saved voice prompt locally)",
            command=self.set_voice_prompt_cache_enabled,
        )
        if self.gui_settings.get("cache_voice_prompts", True):
            self.clone_cache_prompt.select()
        self.clone_cache_prompt.grid(row=8, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.clone_generate_btn = self.glass_button(
            right_col,
            text="Generate Voice Clone",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=46,
            command=self.start_generate_clone,
            variant="primary",
            border_width=2,
        )
        self.clone_generate_btn.grid(row=9, column=0, columnspan=2, padx=10, pady=(18, 10), sticky="ew")

    def setup_design_tab(self):
        self.design_tab.grid_columnconfigure(0, weight=1)
        self.design_tab.grid_columnconfigure(1, weight=1)

        # Left Column - Inputs
        left_col = ctk.CTkFrame(self.design_tab, fg_color="transparent")
        left_col.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_col.grid_columnconfigure(1, weight=1)

        # Text to synthesize
        txt_label = ctk.CTkLabel(left_col, text="Text to Synthesize / Văn bản cần đọc:")
        txt_label.grid(row=0, column=0, sticky="w", pady=(0, 2))
        self.design_expand_btn = self.glass_button(
            left_col,
            text="Mở rộng",
            width=96,
            height=30,
            command=lambda: self.open_text_expander("Mở rộng text Voice Design", self.design_text),
        )
        self.design_expand_btn.grid(row=0, column=1, sticky="e", pady=(0, 2))
        self.design_text = self.styled_textbox(left_col, height=120)
        self.design_text.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        self.design_text.insert(ctk.END, "Hello, this is a test of voice design attributes. I can generate voice based on custom age, gender, and accent.")

        # Dropdowns for Attributes
        self.vd_dropdowns = {}
        row_idx = 2
        for cat, choices in _CATEGORIES.items():
            lbl = ctk.CTkLabel(left_col, text=cat + ":")
            lbl.grid(row=row_idx, column=0, sticky="w", pady=5)
            
            combo = self.styled_combo(left_col, values=["Auto"] + choices)
            combo.set("Auto")
            combo.grid(row=row_idx, column=1, sticky="ew", pady=5)
            self.vd_dropdowns[cat] = combo
            row_idx += 1

        # Language selection
        lang_label = ctk.CTkLabel(left_col, text="Language / Ngôn ngữ:")
        lang_label.grid(row=row_idx, column=0, sticky="w", pady=5)
        
        self.design_lang = "Auto"
        lang_btn_row = ctk.CTkFrame(left_col, fg_color="transparent")
        lang_btn_row.grid(row=row_idx, column=1, sticky="ew", pady=5)
        lang_btn_row.grid_columnconfigure(0, weight=1)
        
        self.design_lang_lbl = ctk.CTkLabel(lang_btn_row, text="Auto", font=ctk.CTkFont(weight="bold"), anchor="w")
        self.design_lang_lbl.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        
        self.design_lang_btn = self.glass_button(lang_btn_row, text="Select", width=100, command=self.choose_design_lang)
        self.design_lang_btn.grid(row=0, column=1, sticky="e")

        # Right Column - Parameters Settings
        right_col = self.soft_panel(self.design_tab)
        right_col.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        right_col.grid_columnconfigure(1, weight=1)

        settings_title = ctk.CTkLabel(right_col, text="Generation Settings", font=ctk.CTkFont(weight="bold", size=14))
        settings_title.grid(row=0, column=0, columnspan=2, pady=10)

        # Inference Steps
        steps_lbl = ctk.CTkLabel(right_col, text="Inference Steps (Mặc định: 32):")
        steps_lbl.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.design_steps = ctk.CTkSlider(right_col, from_=4, to=64, number_of_steps=60)
        self.design_steps.set(32)
        self.design_steps.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        # Guidance Scale
        cfg_lbl = ctk.CTkLabel(right_col, text="Guidance Scale (CFG):")
        cfg_lbl.grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.design_cfg = ctk.CTkSlider(right_col, from_=0.0, to=4.0, number_of_steps=40)
        self.design_cfg.set(2.0)
        self.design_cfg.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        # Speed
        speed_lbl = ctk.CTkLabel(right_col, text="Speed Factor (Tốc độ):")
        speed_lbl.grid(row=3, column=0, padx=10, pady=5, sticky="w")
        self.design_speed = ctk.CTkSlider(right_col, from_=0.5, to=1.5, number_of_steps=20)
        self.design_speed.set(1.0)
        self.design_speed.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        # Duration
        dur_lbl = ctk.CTkLabel(right_col, text="Fixed Duration (s):")
        dur_lbl.grid(row=4, column=0, padx=10, pady=5, sticky="w")
        self.design_duration = self.styled_entry(right_col, placeholder_text="Trống (Tính theo speed)")
        self.design_duration.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        # Checkboxes
        self.design_denoise = ctk.CTkCheckBox(right_col, text="Denoise Audio (Lọc nhiễu)")
        self.design_denoise.select()
        self.design_denoise.grid(row=5, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.design_preprocess = ctk.CTkCheckBox(right_col, text="Preprocess Prompt")
        self.design_preprocess.select()
        self.design_preprocess.grid(row=6, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.design_postprocess = ctk.CTkCheckBox(right_col, text="Postprocess Output")
        self.design_postprocess.select()
        self.design_postprocess.grid(row=7, column=0, columnspan=2, padx=10, pady=5, sticky="w")

        self.design_generate_btn = self.glass_button(
            right_col,
            text="Generate Designed Voice",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=46,
            command=self.start_generate_design,
            variant="primary",
            border_width=2,
        )
        self.design_generate_btn.grid(row=8, column=0, columnspan=2, padx=10, pady=(18, 10), sticky="ew")

    def setup_library_tab(self):
        """Build Split-Screen layout for generated audio records list and detail player."""
        self.library_tab.grid_columnconfigure(0, weight=4)  # Left: List
        self.library_tab.grid_columnconfigure(1, weight=6)  # Right: Detail
        self.library_tab.grid_rowconfigure(0, weight=1)

        # --- Left Side: List Panel ---
        left_panel = self.soft_panel(self.library_tab)
        left_panel.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        left_panel.grid_columnconfigure(0, weight=1)

        left_panel.grid_rowconfigure(0, weight=0)
        left_panel.grid_rowconfigure(1, weight=0)
        left_panel.grid_rowconfigure(2, weight=1)

        # Row 0: Title + Refresh
        header = ctk.CTkFrame(left_panel, fg_color="transparent")
        header.grid(row=0, column=0, padx=10, pady=(10, 4), sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(header, text="Các audio đã tạo ra", font=ctk.CTkFont(weight="bold", size=14))
        title_lbl.grid(row=0, column=0, sticky="w")

        ref_btn = self.glass_button(header, text="Refresh", width=78, command=self.refresh_library_list)
        ref_btn.grid(row=0, column=1, sticky="e")

        # Row 1: Multi-select toolbar
        select_bar = ctk.CTkFrame(left_panel, fg_color="transparent")
        select_bar.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")

        self.select_all_btn = self.glass_button(
            select_bar, text="Chọn tất cả",
            width=100, height=28,
            command=self.select_all_library
        )
        self.select_all_btn.pack(side="left", padx=(0, 4))

        self.deselect_all_btn = self.glass_button(
            select_bar, text="Bỏ chọn",
            width=80, height=28,
            command=self.deselect_all_library
        )
        self.deselect_all_btn.pack(side="left", padx=(0, 8))

        self.delete_selected_btn = self.glass_button(
            select_bar, text="Xóa đã chọn",
            width=110, height=28,
            state="disabled",
            command=self.delete_selected_library,
            variant="danger",
        )
        self.delete_selected_btn.pack(side="left")

        self.selection_count_lbl = ctk.CTkLabel(
            select_bar, text="", text_color="#a0a0a0",
            font=ctk.CTkFont(size=11)
        )
        self.selection_count_lbl.pack(side="right", padx=4)

        # Row 2: Scrollable cards
        self.library_scroll = ctk.CTkScrollableFrame(
            left_panel,
            corner_radius=14,
            fg_color=UI["panel"],
            border_width=1,
            border_color=UI["border"],
        )
        self.library_scroll.grid(row=2, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.library_scroll.grid_columnconfigure(0, weight=1)

        # Lookup: item_id -> (card_frame, item_dict)
        self.card_items = {}

        # --- Right Side: Details View Panel ---
        self.right_lib_frame = self.soft_panel(self.library_tab)
        self.right_lib_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        self.right_lib_frame.grid_columnconfigure(0, weight=1)
        self.right_lib_frame.grid_rowconfigure(5, weight=1)  # Text Box expands

        d_title = ctk.CTkLabel(self.right_lib_frame, text="Chi tiết File Audio", font=ctk.CTkFont(weight="bold", size=14))
        d_title.grid(row=0, column=0, padx=15, pady=10, sticky="w")

        self.lib_meta_mode = ctk.CTkLabel(self.right_lib_frame, text="Phương thức: N/A", anchor="w")
        self.lib_meta_mode.grid(row=1, column=0, padx=15, pady=2, sticky="ew")

        self.lib_meta_time = ctk.CTkLabel(self.right_lib_frame, text="Thời gian tạo: N/A", anchor="w")
        self.lib_meta_time.grid(row=2, column=0, padx=15, pady=2, sticky="ew")

        self.lib_meta_details = ctk.CTkLabel(self.right_lib_frame, text="Chi tiết: N/A", anchor="w", wraplength=400, justify="left")
        self.lib_meta_details.grid(row=3, column=0, padx=15, pady=2, sticky="ew")

        # Full Text display area
        text_lbl = ctk.CTkLabel(self.right_lib_frame, text="Nội dung văn bản (Text):", font=ctk.CTkFont(weight="bold"))
        text_lbl.grid(row=4, column=0, padx=15, pady=(10, 2), sticky="w")

        self.lib_text_box = self.styled_textbox(self.right_lib_frame, wrap="word")
        self.lib_text_box.grid(row=5, column=0, padx=15, pady=(0, 8), sticky="nsew")
        self.lib_text_box.configure(state="disabled")

        # Action buttons row: Play | Edit | Delete
        action_frame = ctk.CTkFrame(self.right_lib_frame, fg_color="transparent")
        action_frame.grid(row=6, column=0, padx=15, pady=(0, 15), sticky="ew")
        action_frame.grid_columnconfigure(0, weight=1)

        self.lib_load_btn = self.glass_button(
            action_frame,
            text="Load & Play Audio",
            state="disabled",
            command=self.load_selected_library_audio,
            variant="primary",
        )
        self.lib_load_btn.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        lib_action_right = ctk.CTkFrame(action_frame, fg_color="transparent")
        lib_action_right.grid(row=0, column=1, sticky="e")

        self.lib_open_path_btn = self.glass_button(
            lib_action_right,
            text="Open Path",
            state="disabled",
            command=self.open_selected_library_audio_path,
            width=105
        )
        self.lib_open_path_btn.pack(side="left", padx=(0, 4))

        self.lib_edit_btn = self.glass_button(
            lib_action_right,
            text="Edit",
            state="disabled",
            command=self.edit_library_item,
            width=130
        )
        self.lib_edit_btn.pack(side="left", padx=(0, 4))

        self.lib_delete_btn = self.glass_button(
            lib_action_right,
            text="Delete",
            state="disabled",
            command=self.delete_library_item,
            width=80,
            variant="danger",
        )
        self.lib_delete_btn.pack(side="left")

        self.selected_lib_item = None
        self.card_widgets = []
        
        # Load initial history list
        self.refresh_library_list()

    # --- Actions / Functions ---

    # Presets Managers
    def update_preset_dropdown(self):
        preset_names = ["-- Chọn mẫu giọng --"] + list(self.presets.keys())
        self.preset_combo.configure(values=preset_names)
        self.preset_combo.set("-- Chọn mẫu giọng --")

    def on_preset_selected(self, name):
        if name in self.presets:
            preset = self.presets[name]
            self.ref_audio_entry.delete(0, ctk.END)
            self.ref_audio_entry.insert(0, preset.get("ref_audio", ""))
            
            self.clone_ref_text.delete(0, ctk.END)
            self.clone_ref_text.insert(0, preset.get("ref_text", ""))
            self.log(f"Loaded voice config preset: '{name}'")

    def save_current_preset(self):
        ref_audio = self.ref_audio_entry.get().strip()
        ref_text = self.clone_ref_text.get().strip()

        if not ref_audio:
            messagebox.showwarning("Warning", "Hãy chọn file âm thanh mẫu hoặc ghi âm trước khi lưu!")
            return

        dialog = ctk.CTkInputDialog(text="Nhập tên mẫu giọng mới:", title="Lưu mẫu giọng")
        preset_name = dialog.get_input()

        if preset_name and preset_name.strip():
            preset_name = preset_name.strip()
            
            # Check overwrite
            if preset_name in self.presets:
                if not messagebox.askyesno("Xác nhận", f"Mẫu giọng '{preset_name}' đã tồn tại. Bạn có muốn ghi đè không?"):
                    return

            self.presets[preset_name] = {
                "ref_audio": ref_audio,
                "ref_text": ref_text
            }
            self.save_presets_to_file()
            self.update_preset_dropdown()
            self.preset_combo.set(preset_name)
            self.log(f"Saved preset: '{preset_name}'")
            messagebox.showinfo("Success", f"Đã lưu mẫu giọng '{preset_name}' thành công!")

    def delete_selected_preset(self):
        selected = self.preset_combo.get()
        if selected == "-- Chọn mẫu giọng --" or selected not in self.presets:
            messagebox.showwarning("Warning", "Hãy chọn một mẫu giọng hợp lệ để xóa!")
            return

        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa mẫu giọng '{selected}' không?"):
            del self.presets[selected]
            self.save_presets_to_file()
            self.update_preset_dropdown()
            self.log(f"Deleted preset: '{selected}'")
            messagebox.showinfo("Success", f"Đã xóa mẫu '{selected}' thành công.")

    # Library History Managers
    def refresh_library_list(self):
        for widget in self.card_widgets:
            try:
                widget.destroy()
            except Exception:
                pass
        self.card_widgets.clear()
        self.card_items.clear()
        self.selected_lib_ids.clear()
        self._update_lib_selection_ui()

        self.history = self.load_history()

        if not self.history:
            no_item = ctk.CTkLabel(self.library_scroll, text="Chưa có file audio nào được tạo.", text_color="gray")
            no_item.grid(row=0, column=0, pady=20)
            self.card_widgets.append(no_item)
            return

        for idx, item in enumerate(self.history):
            item_id = item.get("id", str(idx))
            text = item.get("text", "")
            preview_text = text.replace("\n", " ")
            if len(preview_text) > 55:
                preview_text = preview_text[:55] + "..."

            card = ctk.CTkFrame(
                self.library_scroll,
                corner_radius=12,
                cursor="hand2",
                fg_color=UI["panel_soft"],
                border_width=1,
                border_color=UI["border"],
            )
            card.grid(row=idx, column=0, padx=5, pady=4, sticky="ew")
            card.grid_columnconfigure(0, weight=1)

            mode_lbl = ctk.CTkLabel(
                card,
                text=f"[{item.get('mode')}] - {item.get('timestamp')}",
                font=ctk.CTkFont(weight="bold", size=12),
                text_color=UI["accent"],
                anchor="w"
            )
            mode_lbl.grid(row=0, column=0, padx=10, pady=(5, 2), sticky="w")

            txt_lbl = ctk.CTkLabel(
                card,
                text=preview_text,
                font=ctk.CTkFont(size=11),
                text_color=UI["muted"],
                anchor="w"
            )
            txt_lbl.grid(row=1, column=0, padx=10, pady=(2, 5), sticky="w")

            self.card_widgets.extend([card, mode_lbl, txt_lbl])
            self.card_items[item_id] = (card, item)

            # Normal click = single select + show detail; Ctrl+Click = toggle multi-select
            click_cb = lambda event, i=item, c=card: self.on_library_card_click(event, i, c)
            card.bind("<Button-1>", click_cb)
            mode_lbl.bind("<Button-1>", click_cb)
            txt_lbl.bind("<Button-1>", click_cb)

    def _update_lib_selection_ui(self):
        """Refresh card colors and toolbar counter based on current selection."""
        count = len(self.selected_lib_ids)
        for item_id, (card, _) in self.card_items.items():
            if item_id in self.selected_lib_ids:
                card.configure(fg_color=UI["glass_active"], border_color=UI["border_hot"])
            else:
                card.configure(fg_color=UI["panel_soft"], border_color=UI["border"])
        if count > 0:
            self.delete_selected_btn.configure(state="normal")
            self.selection_count_lbl.configure(text=f"Đã chọn: {count}")
        else:
            self.delete_selected_btn.configure(state="disabled")
            self.selection_count_lbl.configure(text="")

    def on_library_card_click(self, event, item, card_widget):
        item_id = item.get("id", "")
        ctrl_held = bool(event.state & 0x4)  # Ctrl bitmask

        if ctrl_held:
            # Toggle selection
            if item_id in self.selected_lib_ids:
                self.selected_lib_ids.discard(item_id)
            else:
                self.selected_lib_ids.add(item_id)
            self._update_lib_selection_ui()
            count = len(self.selected_lib_ids)
            if count != 1:
                self.lib_meta_mode.configure(text=f"Đang chọn {count} mục")
                self.lib_meta_time.configure(text="Ctrl+Click để chọn/bỏ chọn thêm.")
                self.lib_meta_details.configure(text="")
                self.lib_load_btn.configure(state="disabled")
                self.lib_open_path_btn.configure(state="disabled")
                self.lib_edit_btn.configure(state="disabled")
                self.lib_delete_btn.configure(state="disabled")
                return
        else:
            # Normal click: clear selection, select only this one
            self.selected_lib_ids.clear()
            self.selected_lib_ids.add(item_id)
            self._update_lib_selection_ui()

        # Single item focused — show detail
        self.selected_lib_item = item
        self.lib_meta_mode.configure(text=f"Phương thức: {item.get('mode')}")
        self.lib_meta_time.configure(text=f"Thời gian tạo: {item.get('timestamp')}")
        self.lib_meta_details.configure(text=f"Chi tiết: {item.get('details', '')}")
        self.lib_text_box.configure(state="normal")
        self.lib_text_box.delete("1.0", ctk.END)
        self.lib_text_box.insert(ctk.END, item.get("text", ""))
        self.lib_text_box.configure(state="disabled")
        self.lib_load_btn.configure(state="normal")
        self.lib_open_path_btn.configure(state="normal")
        self.lib_edit_btn.configure(state="normal")
        self.lib_delete_btn.configure(state="normal")

    def select_all_library(self):
        self.selected_lib_ids = set(self.card_items.keys())
        self._update_lib_selection_ui()
        count = len(self.selected_lib_ids)
        self.lib_meta_mode.configure(text=f"Đang chọn tất cả ({count} mục)")
        self.lib_meta_time.configure(text="Nhấn 'Xóa đã chọn' để xóa hàng loạt.")
        self.lib_meta_details.configure(text="")
        self.lib_load_btn.configure(state="disabled")
        self.lib_open_path_btn.configure(state="disabled")
        self.lib_edit_btn.configure(state="disabled")
        self.lib_delete_btn.configure(state="disabled")
        self.selected_lib_item = None

    def deselect_all_library(self):
        self.selected_lib_ids.clear()
        self._update_lib_selection_ui()
        self.selected_lib_item = None
        self.lib_meta_mode.configure(text="Phương thức: N/A")
        self.lib_meta_time.configure(text="Thời gian tạo: N/A")
        self.lib_meta_details.configure(text="Chi tiết: N/A")
        self.lib_text_box.configure(state="normal")
        self.lib_text_box.delete("1.0", ctk.END)
        self.lib_text_box.configure(state="disabled")
        self.lib_load_btn.configure(state="disabled")
        self.lib_open_path_btn.configure(state="disabled")
        self.lib_edit_btn.configure(state="disabled")
        self.lib_delete_btn.configure(state="disabled")

    def delete_selected_library(self):
        """Bulk-delete all items in selected_lib_ids."""
        ids_to_delete = list(self.selected_lib_ids)
        if not ids_to_delete:
            return
        count = len(ids_to_delete)
        msg = f"Bạn có chắc muốn xóa {count} audio đã chọn không?\nTất cả file WAV cũng sẽ bị xóa khỏi ổ cứng!"
        if not messagebox.askyesno("Xác nhận xóa hàng loạt", msg):
            return
        deleted = 0
        for item_id in ids_to_delete:
            item = next((h for h in self.history if h.get("id") == item_id), None)
            if not item:
                continue
            file_path = item.get("file_path", "")
            full_path = os.path.join(os.getcwd(), file_path) if not os.path.isabs(file_path) else file_path
            if os.path.exists(full_path):
                try:
                    os.remove(full_path)
                except Exception as e:
                    pass
            deleted += 1
        self.history = [h for h in self.history if h.get("id") not in set(ids_to_delete)]
        self.save_history_to_file()
        self.log(f"Deleted {deleted} audio file(s) from library.")
        self.selected_lib_item = None
        self.refresh_library_list()
        self.lib_meta_mode.configure(text="Phương thức: N/A")
        self.lib_meta_time.configure(text="Thời gian tạo: N/A")
        self.lib_meta_details.configure(text="Chi tiết: N/A")
        self.lib_text_box.configure(state="normal")
        self.lib_text_box.delete("1.0", ctk.END)
        self.lib_text_box.configure(state="disabled")
        self.lib_load_btn.configure(state="disabled")
        self.lib_open_path_btn.configure(state="disabled")
        self.lib_edit_btn.configure(state="disabled")
        self.lib_delete_btn.configure(state="disabled")

    def delete_library_item(self):
        """Delete single focused item via right-panel Xoa button."""
        if not self.selected_lib_item:
            return
        item_id = self.selected_lib_item.get("id")
        self.selected_lib_ids = {item_id}
        self.delete_selected_library()


    def edit_library_item(self):
        """Copy this item's text and reference audio back to Clone tab for re-generation."""
        if not self.selected_lib_item:
            return

        item = self.selected_lib_item
        text = item.get("text", "")
        details = item.get("details", "")

        # Switch to Clone tab
        self.tabview.set(TAB_CLONE)

        # Fill text to synthesize
        self.clone_text.delete("1.0", ctk.END)
        self.clone_text.insert(ctk.END, text)

        # Try extract original reference audio path from details (e.g. "Voice Clone. Reference: some_file.wav")
        if "Reference:" in details:
            ref_hint = details.split("Reference:", 1)[-1].strip()
            # Check possible absolute or library-relative path
            possible_abs = ref_hint if os.path.isabs(ref_hint) else os.path.join(os.getcwd(), ref_hint)
            possible_lib = os.path.join(self.library_dir, ref_hint)
            
            found_path = ""
            if os.path.exists(possible_abs):
                found_path = possible_abs
            elif os.path.exists(possible_lib):
                found_path = possible_lib

            if found_path:
                self.ref_audio_entry.delete(0, ctk.END)
                self.ref_audio_entry.insert(0, found_path)

        self.log(f"Edit mode: Text and voice loaded from library item ({item.get('timestamp')}). Adjust and click Generate to re-clone.")

    def load_selected_library_audio(self):
        if not self.selected_lib_item:
            return

        file_path = self.selected_lib_item.get("file_path")
        # Handle relative path resolution
        full_path = os.path.join(os.getcwd(), file_path) if not os.path.isabs(file_path) else file_path

        if not os.path.exists(full_path):
            messagebox.showerror("Error", f"Không tìm thấy file âm thanh tại: {full_path}")
            return

        try:
            self.log(f"Loading audio file: {full_path}")
            data, rate = sf.read(full_path)
            
            # Load into seekable player
            self.audio_player.load(data, rate)
            self.last_generated_audio = (rate, data)
            self.last_generated_meta = {
                "mode": self.selected_lib_item.get("mode", "Audio"),
                "text": self.selected_lib_item.get("text", ""),
                "source": "Library",
            }

            # Enable buttons in bottom panel
            self.play_btn.configure(state="normal")
            self.replay_btn.configure(state="normal")
            self.save_btn.configure(state="normal")

            # Pause state and reset slider
            self.play_state = "paused"
            self.play_btn.configure(text="Play")
            self.player_slider.set(0.0)

            duration = self.audio_player.get_duration()
            self.time_label.configure(text=f"00:00 / {self.format_time(duration)}")
            self.status_label.configure(text=f"Loaded: {os.path.basename(full_path)}")

            # Start playing automatically
            self.toggle_play_pause()
        except Exception as e:
            self.log(f"Error loading audio: {e}")
            messagebox.showerror("Error", f"Lỗi đọc file âm thanh:\n{e}")

    def save_to_library(self, text, mode, details=""):
        if not self.last_generated_audio:
            return

        rate, waveform = self.last_generated_audio
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        unique_id = str(int(time.time()))
        filename = f"{timestamp}_{mode}_{unique_id}.wav"
        file_path = os.path.join(self.library_dir, filename)

        try:
            # Write to disk
            sf.write(file_path, waveform, rate)

            # Save metadata
            relative_path = os.path.relpath(file_path, os.getcwd())
            item = {
                "id": unique_id,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "file_path": relative_path,
                "text": text,
                "mode": mode,
                "details": details
            }
            self.history.insert(0, item)  # Newest first
            self.save_history_to_file()
            self.log(f"Saved audio in library folder: {relative_path}")

            # Refresh list UI
            self.refresh_library_list()
        except Exception as e:
            self.log(f"Failed to auto-save to library history: {e}")

    # General Languages selection
    def choose_clone_lang(self):
        LanguageSelectorDialog(self, current_selection=self.clone_lang, callback=self.set_clone_lang)

    def set_clone_lang(self, lang):
        self.clone_lang = lang
        self.clone_lang_lbl.configure(text=lang)
        self.log(f"Clone language set to: {lang}")

    def choose_design_lang(self):
        LanguageSelectorDialog(self, current_selection=self.design_lang, callback=self.set_design_lang)

    def set_design_lang(self, lang):
        self.design_lang = lang
        self.design_lang_lbl.configure(text=lang)
        self.log(f"Design language set to: {lang}")

    def browse_ref_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.wav *.mp3 *.flac *.m4a"), ("All Files", "*.*")]
        )
        if file_path:
            self.ref_audio_entry.delete(0, ctk.END)
            self.ref_audio_entry.insert(0, file_path)
            self.log(f"Selected reference audio: {file_path}")

    def toggle_recording(self):
        if not self.recording:
            self.recording = True
            self.recorded_data = []
            self.record_btn.configure(text="Recording...", fg_color=UI["glass_active"], border_color=UI["danger"])
            self.log("Recording started. Please speak... Click 'Recording...' to stop.")
            
            def callback(indata, frames, time_info, status):
                if status:
                    print(status)
                self.recorded_data.append(indata.copy())

            self.recording_stream = sd.InputStream(samplerate=24000, channels=1, callback=callback)
            self.recording_stream.start()
        else:
            self.recording = False
            self.record_btn.configure(text="Record", fg_color="transparent", border_color=UI["danger"])
            if self.recording_stream:
                self.recording_stream.stop()
                self.recording_stream.close()
                self.recording_stream = None

            if self.recorded_data:
                audio_data = np.concatenate(self.recorded_data, axis=0)
                sf.write(self.recorded_audio_path, audio_data, 24000)
                self.ref_audio_entry.delete(0, ctk.END)
                self.ref_audio_entry.insert(0, self.recorded_audio_path)
                self.log(f"Recording stopped. Voice saved to: {self.recorded_audio_path} ({len(audio_data)/24000:.2f}s)")
            else:
                self.log("Recording stopped, but no audio was captured.")

    # Core Model Generation Actions
    def start_load_model(self):
        model_name = self.model_entry.get().strip()
        if not self.warn_if_blank_model_needs_download(model_name):
            return

        model_name = self.model_entry.get().strip()
        self.load_model_btn.configure(state="disabled", text="Loading...")
        self.set_busy(True)
        device = self.device_combo.get()

        def worker():
            try:
                checkpoint, requested_name = self.resolve_model_checkpoint(model_name)
                self.log(f"Loading model '{requested_name}' on device '{device}'...")
                self.status_label.configure(text="Status: Loading Model...")
                
                self.model = OmniVoice.from_pretrained(
                    checkpoint,
                    device_map=device,
                    dtype=torch.float16 if "cuda" in device or "mps" in device else torch.float32,
                    load_asr=True
                )
                self.loaded_model_name = requested_name
                self.log("Model loaded successfully!")
                self.status_label.configure(text="Status: Model Loaded")
            except Exception as e:
                self.log(f"Error loading model: {e}")
                self.status_label.configure(text="Status: Error loading model")
                messagebox.showerror("Error", f"Failed to load model:\n{e}")
            finally:
                self.load_model_btn.configure(state="normal", text="Load Model")
                self.set_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    def start_generate_clone(self):
        if not self.model:
            messagebox.showwarning("Warning", "Please load the model first!")
            return

        text = self.clone_text.get("1.0", ctk.END).strip()
        ref_audio = self.ref_audio_entry.get().strip()
        ref_text = self.clone_ref_text.get().strip()
        lang = self.clone_lang

        if not text:
            messagebox.showwarning("Warning", "Please enter the text to synthesize!")
            return
        if not ref_audio:
            messagebox.showwarning("Warning", "Please provide a reference audio file or record from microphone first!")
            return

        # Prepare generation config
        steps = int(self.clone_steps.get())
        cfg = float(self.clone_cfg.get())
        speed = float(self.clone_speed.get())
        denoise = self.clone_denoise.get()
        preprocess = self.clone_preprocess.get()
        postprocess = self.clone_postprocess.get()

        duration_val = self.clone_duration.get().strip()
        duration = float(duration_val) if duration_val else None

        self.clone_generate_btn.configure(state="disabled", text="Generating...")
        self.set_busy(True)
        self.status_label.configure(text="Status: Synthesizing Clone...")
        self.play_btn.configure(state="disabled")
        self.replay_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")

        def worker():
            start_time = time.time()
            self.log(f"Synthesizing voice clone... Text: '{text[:40]}...'")
            try:
                gen_config = OmniVoiceGenerationConfig(
                    num_step=steps,
                    guidance_scale=cfg,
                    denoise=denoise,
                    preprocess_prompt=preprocess,
                    postprocess_output=postprocess,
                )

                language = lang if lang != "Auto" else None

                kwargs = {
                    "text": text,
                    "language": language,
                    "generation_config": gen_config
                }

                if speed != 1.0:
                    kwargs["speed"] = speed
                if duration:
                    kwargs["duration"] = duration

                kwargs["voice_clone_prompt"] = self.get_voice_clone_prompt(
                    ref_audio=ref_audio,
                    ref_text=ref_text,
                    preprocess_prompt=preprocess,
                )

                # Generate
                audio_output = self.model.generate(**kwargs)
                waveform = audio_output[0]
                
                # Load to player
                self.audio_player.load(waveform, self.model.sampling_rate)
                self.last_generated_audio = (self.model.sampling_rate, waveform)
                self.last_generated_meta = {
                    "mode": "Clone",
                    "text": text,
                    "details": f"Voice Clone. Reference: {os.path.basename(ref_audio)}",
                }
                
                elapsed = time.time() - start_time
                self.log(f"Synthesized successfully in {elapsed:.2f} seconds!")
                self.status_label.configure(text="Status: Done")
                
                # Auto-save to library folder
                self.save_to_library(text, mode="Clone", details=f"Voice Clone. Reference: {os.path.basename(ref_audio)}")

                # Enable playback and save controls
                self.play_btn.configure(state="normal")
                self.replay_btn.configure(state="normal")
                self.save_btn.configure(state="normal")
                self.play_state = "paused"
                self.play_btn.configure(text="Play")
                self.player_slider.set(0.0)

                duration_sec = self.audio_player.get_duration()
                self.time_label.configure(text=f"00:00 / {self.format_time(duration_sec)}")

                # Auto-play for better UX
                self.toggle_play_pause()
            except Exception as e:
                self.log(f"Error during voice clone generation: {e}")
                self.status_label.configure(text="Status: Generation Failed")
                messagebox.showerror("Generation Error", f"Failed to generate voice clone:\n{e}")
            finally:
                self.clone_generate_btn.configure(state="normal", text="Generate Voice Clone")
                self.set_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    def start_generate_design(self):
        if not self.model:
            messagebox.showwarning("Warning", "Please load the model first!")
            return

        text = self.design_text.get("1.0", ctk.END).strip()
        lang = self.design_lang

        if not text:
            messagebox.showwarning("Warning", "Please enter the text to synthesize!")
            return

        # Build instruct string from attributes
        selected = []
        for cat, combo in self.vd_dropdowns.items():
            val = combo.get()
            if val != "Auto":
                if " / " in val:
                    en, zh = val.split(" / ", 1)
                    if "Dialect" in cat or "Phương ngữ" in cat:
                        selected.append(zh.strip())
                    else:
                        selected.append(en.strip())
                else:
                    selected.append(val)
        
        instruct = ", ".join(selected) if selected else None

        steps = int(self.design_steps.get())
        cfg = float(self.design_cfg.get())
        speed = float(self.design_speed.get())
        denoise = self.design_denoise.get()
        preprocess = self.design_preprocess.get()
        postprocess = self.design_postprocess.get()

        duration_val = self.design_duration.get().strip()
        duration = float(duration_val) if duration_val else None

        self.design_generate_btn.configure(state="disabled", text="Generating...")
        self.set_busy(True)
        self.status_label.configure(text="Status: Synthesizing Designed Voice...")
        self.play_btn.configure(state="disabled")
        self.replay_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")

        def worker():
            start_time = time.time()
            self.log(f"Synthesizing voice design... Instruct: '{instruct}'. Text: '{text[:40]}...'")
            try:
                gen_config = OmniVoiceGenerationConfig(
                    num_step=steps,
                    guidance_scale=cfg,
                    denoise=denoise,
                    preprocess_prompt=preprocess,
                    postprocess_output=postprocess,
                )

                language = lang if lang != "Auto" else None

                kwargs = {
                    "text": text,
                    "language": language,
                    "generation_config": gen_config
                }

                if speed != 1.0:
                    kwargs["speed"] = speed
                if duration:
                    kwargs["duration"] = duration
                if instruct:
                    kwargs["instruct"] = instruct

                # Generate
                audio_output = self.model.generate(**kwargs)
                waveform = audio_output[0]
                
                # Load to player
                self.audio_player.load(waveform, self.model.sampling_rate)
                self.last_generated_audio = (self.model.sampling_rate, waveform)
                self.last_generated_meta = {
                    "mode": "Design",
                    "text": text,
                    "details": f"Voice Design. Instruct: {instruct or 'None'}",
                }
                
                elapsed = time.time() - start_time
                self.log(f"Synthesized successfully in {elapsed:.2f} seconds!")
                self.status_label.configure(text="Status: Done")
                
                # Auto-save to library folder
                self.save_to_library(text, mode="Design", details=f"Voice Design. Instruct: {instruct or 'None'}")

                # Enable controls
                self.play_btn.configure(state="normal")
                self.replay_btn.configure(state="normal")
                self.save_btn.configure(state="normal")
                self.play_state = "paused"
                self.play_btn.configure(text="Play")
                self.player_slider.set(0.0)

                duration_sec = self.audio_player.get_duration()
                self.time_label.configure(text=f"00:00 / {self.format_time(duration_sec)}")

                # Auto-play for better UX
                self.toggle_play_pause()
            except Exception as e:
                self.log(f"Error during voice design generation: {e}")
                self.status_label.configure(text="Status: Generation Failed")
                messagebox.showerror("Generation Error", f"Failed to generate designed voice:\n{e}")
            finally:
                self.design_generate_btn.configure(state="normal", text="Generate Designed Voice")
                self.set_busy(False)

        threading.Thread(target=worker, daemon=True).start()

    # Audio Playback Control Actions
    def toggle_play_pause(self):
        if self.audio_player.data is None:
            return

        if self.play_state == "paused":
            self.play_state = "playing"
            self.play_btn.configure(text="Pause")
            self.audio_player.play()
        else:
            self.play_state = "paused"
            self.play_btn.configure(text="Play")
            self.audio_player.pause()

    def replay_audio(self):
        if self.audio_player.data is None:
            return

        self.audio_player.stop()
        self.audio_player.seek(0)
        self.player_slider.set(0.0)

        duration = self.audio_player.get_duration()
        self.time_label.configure(text=f"00:00 / {self.format_time(duration)}")

        self.play_state = "playing"
        self.play_btn.configure(text="Pause")
        self.audio_player.play()

    def on_slider_drag(self, value):
        if self.audio_player.data is not None:
            duration = self.audio_player.get_duration()
            target_time = value * duration
            self.audio_player.seek(target_time)
            self.time_label.configure(text=f"{self.format_time(target_time)} / {self.format_time(duration)}")

    def save_audio_legacy(self):
        if not self.last_generated_audio:
            return
        
        rate, waveform = self.last_generated_audio
        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV Audio Files", "*.wav")],
            title="Lưu file âm thanh đã sinh"
        )
        if file_path:
            try:
                sf.write(file_path, waveform, rate)
                self.remember_save_dir(file_path)
                self.log(f"Audio saved to: {file_path}")
                self.show_saved_success(file_path)
            except Exception as e:
                self.log(f"Error saving audio: {e}")
                messagebox.showerror("Error", f"Failed to save audio:\n{e}")

    def save_audio(self):
        if not self.last_generated_audio:
            return

        rate, waveform = self.last_generated_audio
        default_dir = self.gui_settings.get("last_save_dir") or os.getcwd()
        if not os.path.isdir(default_dir):
            default_dir = os.getcwd()

        file_path = filedialog.asksaveasfilename(
            defaultextension=".wav",
            filetypes=[("WAV Audio Files", "*.wav")],
            title="Lưu file âm thanh đã sinh",
            initialdir=default_dir,
            initialfile=self.smart_filename(),
        )
        if file_path:
            try:
                sf.write(file_path, waveform, rate)
                self.remember_save_dir(file_path)
                self.log(f"Audio saved to: {file_path}")
                self.show_saved_success(file_path)
            except Exception as e:
                self.log(f"Error saving audio: {e}")
                messagebox.showerror("Error", f"Failed to save audio:\n{e}")


if __name__ == "__main__":
    app = OmniVoiceGUI()
    app.mainloop()
