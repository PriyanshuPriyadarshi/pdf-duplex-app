import re

with open('src/print_wizard.py', 'r') as f:
    content = f.read()

content = content.replace(
    'self.invert = settings.get("invert_colors", False)',
    'self.invert = settings.get("invert_colors", False)\n        self.print_page_numbers = settings.get("print_page_numbers", False)\n        self.page_number_pos = settings.get("page_number_pos", "Bottom Right")'
)

content = content.replace(
    'self.pass1_bytes = imposer.impose_normal(self.pdf_path, self.invert)',
    'self.pass1_bytes = imposer.impose_normal(self.pdf_path, self.invert, self.print_page_numbers, self.page_number_pos)'
)

content = content.replace(
    'self.pass1_bytes, self.pass2_bytes = imposer.get_duplex_passes(\n                    self.pdf_path, self.reverse_backs, self.invert\n                )',
    'self.pass1_bytes, self.pass2_bytes = imposer.get_duplex_passes(\n                    self.pdf_path, self.reverse_backs, self.invert, self.print_page_numbers, self.page_number_pos\n                )'
)

content = content.replace(
    'self.pass1_bytes, self.pass2_bytes = imposer.get_booklet_passes(\n                    self.pdf_path, self.reverse_backs, self.invert\n                )',
    'self.pass1_bytes, self.pass2_bytes = imposer.get_booklet_passes(\n                    self.pdf_path, self.reverse_backs, self.invert, self.print_page_numbers, self.page_number_pos\n                )'
)

with open('src/print_wizard.py', 'w') as f:
    f.write(content)
