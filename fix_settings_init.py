import re

with open('src/settings_panel.py', 'r') as f:
    content = f.read()

get_settings_safe = '''
    def get_settings(self) -> dict:
        print_page_numbers = getattr(self, "check_page_numbers", None)
        print_page_numbers = print_page_numbers.isChecked() if print_page_numbers else False
        
        page_number_pos = getattr(self, "combo_page_num_pos", None)
        page_number_pos = page_number_pos.currentText() if page_number_pos else "Bottom Right"

        return {
            "mode": self.get_current_mode(),
            "flip_edge": "short" if "Short" in getattr(self, "combo_flip", self).currentText() else "long",
            "reverse_backs": getattr(self, "chk_reverse_backs", self).isChecked(),
            "printer": getattr(self, "combo_printer", self).currentText(),
            "copies": getattr(self, "spin_copies", self).value(),
            "invert_colors": False,
            "print_page_numbers": print_page_numbers,
            "page_number_pos": page_number_pos,
        }
'''

content = re.sub(r'def get_settings\(self\) -> dict:.*?\}', get_settings_safe.strip(), content, flags=re.DOTALL)

with open('src/settings_panel.py', 'w') as f:
    f.write(content)
