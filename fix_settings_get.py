import re

with open('src/settings_panel.py', 'r') as f:
    content = f.read()

get_settings_correct = '''
    def get_settings(self) -> dict:
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

content = re.sub(r'def get_settings\(self\) -> dict:.*?\}', get_settings_correct.strip(), content, flags=re.DOTALL)

with open('src/settings_panel.py', 'w') as f:
    f.write(content)
