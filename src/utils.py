"""
src/utils.py - Printing and system utility functions.
Handles CUPS / lp printer discovery, raw print spooling, and temporary file management.
"""

import os
import tempfile
import subprocess
from typing import List, Optional


def get_available_printers() -> List[str]:
    """
    Discover printers configured in the Linux system via CUPS or lpstat.
    Returns a list of printer names.
    """
    printers = []

    # 1. Try lpstat -e (lists active printer destinations)
    try:
        res = subprocess.run(
            ["lpstat", "-e"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                p = line.strip()
                if p and p not in printers:
                    printers.append(p)
            if printers:
                return printers
    except Exception:
        pass

    # 2. Try lpstat -p (standard printer status list)
    try:
        res = subprocess.run(
            ["lpstat", "-p"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2 and parts[0] == "printer":
                    p = parts[1]
                    if p not in printers:
                        printers.append(p)
            if printers:
                return printers
    except Exception:
        pass

    return printers


def print_pdf_bytes(
    pdf_bytes: bytes,
    printer_name: Optional[str] = None,
    copies: int = 1,
) -> None:
    """
    Send raw PDF bytes to the specified CUPS printer via lp.
    Raises RuntimeError if printing fails.
    """
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

        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() or e.stdout.strip() or str(e)
        raise RuntimeError(f"Printer error: {err}")
    except FileNotFoundError:
        raise RuntimeError("The 'lp' printing command is not found on your system.")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def print_pdf(pdf_bytes: bytes, is_duplex: bool = False) -> None:
    """Compatibility wrapper for printing raw PDF bytes."""
    print_pdf_bytes(pdf_bytes)


def show_flip_prompt(parent=None) -> bool:
    """Show a prompt asking user to flip stack and reinsert."""
    from PyQt6.QtWidgets import QMessageBox
    reply = QMessageBox.question(
        parent,
        "Flip Paper",
        "Print the first side? After printing, flip the entire stack and reinsert the paper.\n\nClick OK when you have reinserted the stack.",
        QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        QMessageBox.StandardButton.Ok,
    )
    return reply == QMessageBox.StandardButton.Ok