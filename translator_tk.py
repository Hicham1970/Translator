import tkinter as tk
from tkinter import ttk, messagebox
from deep_translator import GoogleTranslator

import threading
import tempfile
import os
from gtts import gTTS
try:
    from playsound import playsound
except Exception:
    playsound = None


def build_language_mappings():
    """
    Fetch supported languages from deep_translator and build mappings:
    - display_names: list of names shown in the UI (Title Case), including 'Auto (détection)'
    - name_to_code: map from display name -> code (e.g., 'French' -> 'fr')
    """
    try:
        # get_supported_languages works as class or instance method; using instance for compatibility
        langs_dict = GoogleTranslator(source='auto', target='en').get_supported_languages(as_dict=True)
    except TypeError:
        # Fallback in case some versions only accept no args and return list of names
        langs_list = GoogleTranslator(source='auto', target='en').get_supported_languages()
        # Without codes we cannot translate reliably; inform user via UI later if needed
        langs_dict = {name: name for name in langs_list}

    # Normalize to Title Case for display
    name_to_code = {name.title(): code for name, code in langs_dict.items()}

    # Ensure unique display names (some may already be title-cased properly)
    display_names = sorted(name_to_code.keys())

    # Add Auto detection to source list
    auto_display = 'Auto (détection)'
    name_to_code[auto_display] = 'auto'
    display_names = [auto_display] + display_names

    return display_names, name_to_code


def find_display_name_for_code(name_to_code, code, default_display=None):
    for display, c in name_to_code.items():
        if c == code:
            return display
    return default_display


class TranslatorApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Traducteur')
        self.geometry('800x500')
        self.minsize(700, 420)

        # Languages
        self.display_names, self.name_to_code = build_language_mappings()

        # Top controls frame
        controls = ttk.Frame(self, padding=(10, 10, 10, 0))
        controls.grid(row=0, column=0, sticky='ew')
        controls.columnconfigure(1, weight=1)
        controls.columnconfigure(4, weight=1)

        # Source language selector
        ttk.Label(controls, text='Langue source:').grid(row=0, column=0, sticky='w', padx=(0, 8))
        self.src_var = tk.StringVar()
        self.src_combo = ttk.Combobox(controls, textvariable=self.src_var, values=self.display_names, state='readonly')
        self.src_combo.grid(row=0, column=1, sticky='ew')

        # Swap button
        self.swap_btn = ttk.Button(controls, text='⟷', width=3, command=self.swap_languages)
        self.swap_btn.grid(row=0, column=2, padx=8)

        # Target language selector
        ttk.Label(controls, text='Langue cible:').grid(row=0, column=3, sticky='e', padx=(0, 8))
        self.tgt_var = tk.StringVar()
        self.tgt_combo = ttk.Combobox(controls, textvariable=self.tgt_var, values=[n for n in self.display_names if self.name_to_code.get(n) != 'auto'], state='readonly')
        self.tgt_combo.grid(row=0, column=4, sticky='ew')

        # Main panes for input/output
        io_pane = ttk.Frame(self, padding=10)
        io_pane.grid(row=1, column=0, sticky='nsew')
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        io_pane.columnconfigure(0, weight=1)
        io_pane.columnconfigure(2, weight=1)
        io_pane.rowconfigure(1, weight=1)

        # Input
        ttk.Label(io_pane, text='Texte à traduire:').grid(row=0, column=0, sticky='w', pady=(0, 4))
        self.input_text = tk.Text(io_pane, wrap='word', height=10)
        self.input_text.grid(row=1, column=0, sticky='nsew')

        # Translate button centered between panes
        self.translate_btn = ttk.Button(io_pane, text='Traduire', command=self.translate)
        self.translate_btn.grid(row=1, column=1, padx=10)

        # Speech (read aloud) button
        self.speak_btn = ttk.Button(io_pane, text='Lire', command=self.speak_translated, state='disabled')
        self.speak_btn.grid(row=2, column=1, pady=(8, 0))

        # Output
        ttk.Label(io_pane, text='Texte traduit:').grid(row=0, column=2, sticky='w', pady=(0, 4))
        self.output_text = tk.Text(io_pane, wrap='word', height=10, state='disabled')
        self.output_text.grid(row=1, column=2, sticky='nsew')

        # Status bar
        self.status_var = tk.StringVar(value='Prêt')
        status = ttk.Label(self, textvariable=self.status_var, relief='sunken', anchor='w', padding=(8, 2))
        status.grid(row=2, column=0, sticky='ew')

        # Defaults similar to original script
        default_src_display = find_display_name_for_code(self.name_to_code, 'fr', default_display='Auto (détection)')
        default_tgt_display = find_display_name_for_code(self.name_to_code, 'tr', default_display=None)

        try:
            self.src_combo.set(default_src_display)
        except Exception:
            self.src_combo.current(0)
        if default_tgt_display:
            self.tgt_combo.set(default_tgt_display)
        else:
            # Fallback to English if Turkish not present for some reason
            fallback_tgt = find_display_name_for_code(self.name_to_code, 'en', default_display=None)
            if fallback_tgt:
                self.tgt_combo.set(fallback_tgt)
            else:
                self.tgt_combo.current(0)

    def swap_languages(self):
        src = self.src_var.get()
        tgt = self.tgt_var.get()
        # Avoid setting target to Auto
        if src and tgt:
            self.src_combo.set(tgt)
            # If swapped source becomes Auto, keep target unchanged
            if self.name_to_code.get(src) != 'auto':
                self.tgt_combo.set(src)

    def translate(self):
        text = self.input_text.get('1.0', 'end').strip()
        if not text:
            messagebox.showinfo('Information', 'Veuillez saisir un texte à traduire.')
            return

        src_display = self.src_var.get() or 'Auto (détection)'
        tgt_display = self.tgt_var.get()
        src_code = self.name_to_code.get(src_display, 'auto')
        tgt_code = self.name_to_code.get(tgt_display)

        if not tgt_code or tgt_code == 'auto':
            messagebox.showerror('Erreur', 'Veuillez choisir une langue cible valide.')
            return

        self.status_var.set('Traduction en cours...')
        self.translate_btn.configure(state='disabled')
        self.update_idletasks()
        try:
            translator = GoogleTranslator(source=src_code, target=tgt_code)
            translated = translator.translate(text)
        except Exception as exc:
            messagebox.showerror('Erreur', f'La traduction a échoué: {exc}')
            self.status_var.set('Erreur de traduction')
            self.translate_btn.configure(state='normal')
            return

        self.output_text.configure(state='normal')
        self.output_text.delete('1.0', 'end')
        self.output_text.insert('1.0', translated)
        self.output_text.configure(state='disabled')
        # Enable speech button once we have output
        self.speak_btn.configure(state='normal')
        self.status_var.set('Traduction terminée')
        self.translate_btn.configure(state='normal')

    def speak_translated(self):
        text = self.output_text.get('1.0', 'end').strip()
        if not text:
            messagebox.showinfo('Information', 'Rien à lire. Traduisez d\'abord un texte.')
            return

        tgt_display = self.tgt_var.get()
        tgt_code = self.name_to_code.get(tgt_display, 'en')

        if playsound is None:
            messagebox.showerror('Erreur', 'Module de lecture audio indisponible. Installez playsound et gTTS:\n\n    pip install playsound gTTS')
            return

        # Disable speak button during playback
        self.speak_btn.configure(state='disabled')
        self.status_var.set('Synthèse vocale en cours...')

        def worker():
            temp_path = None
            try:
                tts = gTTS(text=text, lang=tgt_code)
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                    temp_path = f.name
                tts.save(temp_path)
                playsound(temp_path)
            except Exception as exc:
                err_msg = f'La lecture a échoué: {exc}'
                self.after(0, lambda m=err_msg: messagebox.showerror('Erreur', m))
            finally:
                if temp_path and os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                self.after(0, lambda: (self.status_var.set('Prêt'), self.speak_btn.configure(state='normal')))

        threading.Thread(target=worker, daemon=True).start()

    



if __name__ == '__main__':
    app = TranslatorApp()
    app.mainloop()
