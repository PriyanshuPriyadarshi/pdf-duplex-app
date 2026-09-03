"""
src/utils.py - Printing and system utility functions.
Handles CUPS / lp printer discovery, raw print spooling, and temporary file management.
"""

import os
import tempfile
import subprocess
from typing import List, Optional


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


def parse_page_range(range_str: str, max_pages: int) -> List[int]:
    """Parse a string like '1-5, 8, 11-13' into a list of 0-indexed integers."""
    if not range_str.strip():
        return list(range(max_pages))
    
    pages = set()
    for part in range_str.split(','):
        part = part.strip()
        if not part: continue
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                if start > end: start, end = end, start
                pages.update(range(max(1, start) - 1, min(max_pages, end)))
            except ValueError: pass
        else:
            try:
                p = int(part)
                if 1 <= p <= max_pages:
                    pages.add(p - 1)
            except ValueError: pass
    return sorted(list(pages))


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


def get_available_printers() -> List[str]:
    """
    Get a list of available printers on the system using CUPS lpstat.
    Returns an empty list if no printers are found or on error.
    """
    try:
        # Run lpstat -p to get printer status
        result = subprocess.run(
            ['lpstat', '-p'], 
            capture_output=True, 
            text=True, 
            timeout=5
        )
        
        if result.returncode != 0:
            # If lpstat fails, try lpstat -s to get system status
            result = subprocess.run(
                ['lpstat', '-s'], 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            if result.returncode != 0:
                return []
        
        # Parse the output to extract printer names
        printers = []
        for line in result.stdout.split('\n'):
            line = line.strip()
            if line.startswith('printer '):
                # Format: "printer printer_name is idle. enabled since ..."
                parts = line.split()
                if len(parts) >= 2:
                    printers.append(parts[1])
            elif line and not line.startswith(' '):
                # Alternative format for lpstat -s
                # Might be like "printer printer_name description"
                parts = line.split()
                if len(parts) >= 2 and parts[0] == 'printer':
                    printers.append(parts[1])
        
        return printers
    except Exception:
        # Return empty list on any error (command not found, timeout, etc.)
        return []

