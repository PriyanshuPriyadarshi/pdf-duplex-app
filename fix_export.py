import re

with open('src/main_window.py', 'r') as f:
    content = f.read()

export_patch = '''
            print_page_numbers = settings.get("print_page_numbers", False)
            page_number_pos = settings.get("page_number_pos", "Bottom Right")

            if mode == "Booklet":
                pdf_bytes = imposer.impose_booklet(
                    self.current_file_path,
                    invert=invert,
                    print_page_numbers=print_page_numbers,
                    page_number_pos=page_number_pos
                )
            elif mode == "Manual Duplex":
                pdf_bytes = imposer.impose_duplex_combined(
                    self.current_file_path,
                    invert=invert,
                    print_page_numbers=print_page_numbers,
                    page_number_pos=page_number_pos
                )
            else:
                pdf_bytes = imposer.impose_normal(
                    self.current_file_path,
                    invert=invert,
                    print_page_numbers=print_page_numbers,
                    page_number_pos=page_number_pos
                )
'''
content = re.sub(r'if mode == "Booklet":.*invert=invert,\n                \)', export_patch.strip(), content, flags=re.DOTALL)

with open('src/main_window.py', 'w') as f:
    f.write(content)
