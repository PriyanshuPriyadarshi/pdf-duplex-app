# tests/test_gui.py
import pytest
from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow
import os
import tempfile
from reportlab.pdfgen import canvas
import io
from unittest.mock import patch

@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])

def test_main_window_creation(app):
    win = MainWindow()
    assert win is not None
    win.deleteLater()

def test_load_pdf_and_preview(app, tmp_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, "Test PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    win = MainWindow()
    win.load_pdf(str(pdf_path))
    assert win.pdf_doc.pageCount() == 1
    win.deleteLater()

def test_print_normal_mode(app, tmp_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, "Test PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    win = MainWindow()
    win.load_pdf(str(pdf_path))
    # Switch to normal mode (already default)
    # Mock the print_pdf function to avoid actual printing
    with patch('src.main_window.print_pdf') as mock_print:
        win.print_document()
        mock_print.assert_called_once()
        # Check that the argument is bytes and is_duplex=False
        args, kwargs = mock_print.call_args
        assert isinstance(args[0], bytes)
        # is_duplex is passed as keyword argument
        assert kwargs.get('is_duplex') == False
    win.deleteLater()

def test_print_duplex_mode(app, tmp_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, "Test PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    win = MainWindow()
    win.load_pdf(str(pdf_path))
    # Set mode to Manual Duplex
    win.mode_combo.setCurrentText("Manual Duplex")
    # We need to mock show_flip_prompt to return True (so it proceeds to second side)
    # and mock print_pdf to capture calls.
    with patch('src.main_window.show_flip_prompt', return_value=True) as mock_flip, \
         patch('src.main_window.print_pdf') as mock_print:
        win.print_document()
        # We expect two calls to print_pdf (first side and second side)
        assert mock_print.call_count == 2
        # Both calls should have is_duplex=False (because we handle flipping manually)
        for call in mock_print.call_args_list:
            args, kwargs = call
            assert isinstance(args[0], bytes)
            # is_duplex is passed as keyword argument
            assert kwargs.get('is_duplex') == False
        # And show_flip_prompt should have been called once
        mock_flip.assert_called_once()
    win.deleteLater()

def test_print_booklet_mode(app, tmp_path):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 700, "Test PDF")
    c.showPage()
    c.save()
    buffer.seek(0)
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, "wb") as f:
        f.write(buffer.getvalue())

    win = MainWindow()
    win.load_pdf(str(pdf_path))
    win.mode_combo.setCurrentText("Booklet")
    with patch('src.main_window.show_flip_prompt', return_value=True) as mock_flip, \
         patch('src.main_window.print_pdf') as mock_print:
        win.print_document()
        assert mock_print.call_count == 2
        for call in mock_print.call_args_list:
            args, kwargs = call
            assert isinstance(args[0], bytes)
            # is_duplex is passed as keyword argument
            assert kwargs.get('is_duplex') == False
        mock_flip.assert_called_once()
    win.deleteLater()