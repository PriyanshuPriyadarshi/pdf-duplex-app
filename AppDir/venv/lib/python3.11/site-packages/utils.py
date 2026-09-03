# src/utils.py
import os
import tempfile
import subprocess
from typing import List

def print_pdf(pdf_bytes: bytes, is_duplex: bool = False) -> None:
    """
    Print the given PDF bytes using the system's lp command.
    If is_duplex is True, we set the sides option to two-sided long-edge.
    Note: This relies on the printer supporting duplex via CUPS.
    For manual duplex, we rely on the caller to flip the stack.
    Here we just print the PDF; the duplex option is set if is_duplex is True.
    """
    # Write to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name
    try:
        cmd = ['lp', tmp_path]
        if is_duplex:
            # Request two-sided printing (long edge) if the printer supports it.
            # For manual duplex, we still set this but the user will flip.
            # We'll use 'sides=two-sided-long-edge'
            cmd.extend(['-o', 'sides=two-sided-long-edge'])
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

def show_flip_prompt(parent=None) -> bool:
    """
    Show a message box asking the user to flip the stack and reinsert.
    Returns True if user clicked OK, False if cancelled.
    This is a placeholder; the actual implementation will be in the GUI.
    """
    from PyQt6.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        parent,
        "Flip Paper",
        "Print the first side? After printing, flip the entire stack and reinsert the paper.\n\nClick OK when you have reinserted the stack.",
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Ok,
    )
    return reply == QMessageBox.StandardButton.Ok