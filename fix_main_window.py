import re

with open('src/main_window.py', 'r') as f:
    content = f.read()

update_preview_patch = '''
        self.center_preview.set_document(self.doc)
        self.center_preview.set_mode(settings["mode"])
        self.center_preview.set_page_number_settings(
            settings.get("print_page_numbers", False),
            settings.get("page_number_pos", "Bottom Right")
        )
        self.center_preview.update_preview()
'''
content = re.sub(r'self\.center_preview\.set_document\(self\.doc\)\s+self\.center_preview\.set_mode\(settings\["mode"\]\)\s+self\.center_preview\.update_preview\(\)', update_preview_patch.strip(), content)

with open('src/main_window.py', 'w') as f:
    f.write(content)
