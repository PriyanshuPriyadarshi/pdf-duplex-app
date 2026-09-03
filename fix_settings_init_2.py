import re

with open('src/settings_panel.py', 'r') as f:
    content = f.read()

get_settings_safe = '''
    def get_settings(self) -> dict:
        # Prevent accessing widgets before setup completes
        if not hasattr(self, "combo_printer") or not hasattr(self, "check_page_numbers"):
            return {
                "mode": "Normal",
                "flip_edge": "long",
                "reverse_backs": False,
                "printer": "Save as PDF File",
                "copies": 1,
                "invert_colors": False,
                "print_page_numbers": False,
                "page_number_pos": "Bottom Right"
            }

        return {
            "mode": self.get_current_mode(),
            "flip_edge": "short" if "Short" in self.combo_flip.currentText() else "long",
            "reverse_backs": self.chk_reverse_backs.isChecked(),
            "printer": self.combo_printer.currentText(),
            "copies": self.spin_copies.value(),
            "invert_colors": False,
            "print_page_numbers": self.check_page_numbers.isChecked(),
            "page_number_pos": self.combo_page_num_pos.currentText(),
        }
'''

content = re.sub(r'def get_settings\(self\) -> dict:.*?\}', get_settings_safe.strip(), content, flags=re.DOTALL)

with open('src/settings_panel.py', 'w') as f:
    f.write(content)
