# run.py
#!/usr/bin/env python3
"""
Run the PDF Duplex/Booklet Printer GUI.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from main_window import main

if __name__ == "__main__":
    main()