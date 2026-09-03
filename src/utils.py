"""
src/utils.py - Printing and system utility functions.
Handles CUPS / lp printer discovery, raw print spooling, and temporary file management.
"""

import os
import tempfile
import subprocess
from typing import List, Optional


def get_available_printers() -> List[str]:
    printers = []
    try:
        res = subprocess.run(["lpstat", "-e"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in printers: printers.append(p)
            if printers: return printers
    except Exception: pass

    try:
        res = subprocess.run(["lpstat", "-p"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "printer":
                    p = parts[1]
                    if p not in printers: printers.append(p)
            if printers: return printers
    except Exception: pass
    return printers


def print_pdf_bytes(pdf_bytes: bytes, printer_name: Optional[str] = None, copies: int = 1) -> None:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(pdf_bytes)
        tmp_path = tmp.name

    try:
        cmd = ["lp"]
        if printer_name and printer_name not in ("Default System Printer", "Save as PDF File"):
            cmd.extend(["-d", printer_name])
        if copies > 1:
            cmd.extend(["-n", str(copies)])
        cmd.append(tmp_path)
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() or e.stdout.strip() or str(e)
        if "No default destination" in err or "no default" in err.lower():
            raise RuntimeError("No default printer is configured on your system.\n\nPlease select a specific printer from the dropdown menu in the right panel.")
        raise RuntimeError(f"Printer error: {err}")
    except FileNotFoundError:
        raise RuntimeError("The 'lp' printing command is not found on your system.")
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass

def print_pdf(pdf_bytes: bytes, is_duplex: bool = False) -> None:
    print_pdf_bytes(pdf_bytes)

def show_flip_prompt(parent=None) -> bool:
    from PyQt6.QtWidgets import QMessageBox
    reply = QMessageBox.question(parent, "Flip Paper", "Print the first side? After printing, flip the entire stack and reinsert the paper.\n\nClick OK when you have reinserted the stack.", QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Ok)
    return reply == QMessageBox.StandardButton.Ok
