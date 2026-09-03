import re

with open('src/settings_panel.py', 'r') as f:
    content = f.read()

settings_ui_add = '''
        # Page Numbers
        self.group_page_num = QGroupBox("PAGE NUMBERS")
        page_num_layout = QVBoxLayout()
        page_num_layout.setContentsMargins(8, 12, 8, 8)
        page_num_layout.setSpacing(10)

        self.check_page_numbers = QCheckBox("Add Page Numbers to PDF")
        self.check_page_numbers.setChecked(False)
        self.check_page_numbers.stateChanged.connect(lambda: self.settings_changed.emit())
        page_num_layout.addWidget(self.check_page_numbers)

        pos_layout = QHBoxLayout()
        pos_layout.addWidget(QLabel("Position:"))
        self.combo_page_num_pos = QComboBox()
        self.combo_page_num_pos.addItems([
            "Bottom Right", "Bottom Center", "Bottom Left",
            "Top Right", "Top Center", "Top Left"
        ])
        self.combo_page_num_pos.currentIndexChanged.connect(lambda: self.settings_changed.emit())
        pos_layout.addWidget(self.combo_page_num_pos)
        page_num_layout.addLayout(pos_layout)
        
        self.group_page_num.setLayout(page_num_layout)
        main_layout.addWidget(self.group_page_num)

        main_layout.addStretch()
'''
content = content.replace('main_layout.addStretch()', settings_ui_add.strip())

get_settings_replace = '''
    def get_settings(self) -> dict:
        return {
            "mode": self.combo_mode.currentText(),
            "flip_edge": "short" if self.radio_short.isChecked() else "long",
            "reverse_backs": self.check_reverse.isChecked(),
            "printer": self.combo_printer.currentText(),
            "copies": self.spin_copies.value(),
            "invert_colors": self.combo_invert.currentText() == "Yes",
            "print_page_numbers": self.check_page_numbers.isChecked(),
            "page_number_pos": self.combo_page_num_pos.currentText(),
        }
'''
content = re.sub(r'def get_settings\(self\) -> dict:.*?\}', get_settings_replace.strip(), content, flags=re.DOTALL)

with open('src/settings_panel.py', 'w') as f:
    f.write(content)
