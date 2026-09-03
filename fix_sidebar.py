import re

with open('src/sidebar_page_list.py', 'r') as f:
    content = f.read()

# Fix ThumbnailCard __init__ to set objectName
content = content.replace(
    'super().__init__(parent)',
    'super().__init__(parent)\n        self.setObjectName("thumbnailCard")'
)

# Fix update_style
old_style = '''        if self.is_selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #382424;
                    border: 2px solid #E64B3D;
                    border-radius: 0px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #212126;
                    border: 1px solid #3e4451;
                    border-radius: 0px;
                }
                QFrame:hover {
                    background-color: #28282E;
                    border: 1px solid #5c6370;
                }
            """)'''

new_style = '''        if self.is_selected:
            self.setStyleSheet("""
                QFrame#thumbnailCard {
                    background-color: #212126;
                    border: 2px solid #E64B3D;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame#thumbnailCard {
                    background-color: #212126;
                    border: 1px solid #36363D;
                    border-radius: 8px;
                }
                QFrame#thumbnailCard:hover {
                    background-color: #28282E;
                    border: 1px solid #636363;
                }
            """)'''

if old_style in content:
    content = content.replace(old_style, new_style)
else:
    # Just in case my previous script altered the colors
    import ast
    # We will regex replace the QFrame styles
    content = re.sub(
        r'if self\.is_selected:\s*self\.setStyleSheet\(\"\"\"\s*QFrame\s*\{[^\}]+\}\s*\"\"\"\)\s*else:\s*self\.setStyleSheet\(\"\"\"\s*QFrame\s*\{[^\}]+\}\s*QFrame:hover\s*\{[^\}]+\}\s*\"\"\"\)',
        new_style.strip(),
        content
    )

with open('src/sidebar_page_list.py', 'w') as f:
    f.write(content)
