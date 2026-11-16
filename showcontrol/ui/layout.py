"""Przybornik do budowy prostego układu głównego okna operatora."""

from __future__ import annotations

from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget


def build_layout_container(parent=None):
    """Tworzy główny kontener okna i prosty układ pionowy."""
    container = QWidget(parent)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(15, 15, 15, 15)
    layout.setSpacing(10)
    return container, layout


def build_top_bar():
    """Zwraca układ poziomy dla sekcji poleceń głównych."""
    return QHBoxLayout()


def build_row():
    """Zwraca układ poziomy z domyślnym odstępem."""
    layout = QHBoxLayout()
    layout.setSpacing(6)
    return layout


def build_panel_row():
    """Zwraca układ poziomy do ładowania paneli."""
    layout = QHBoxLayout()
    layout.setSpacing(12)
    return layout


def build_vertical_panel():
    """Zwraca układ pionowy dla sekcji operatora."""
    layout = QVBoxLayout()
    layout.setSpacing(6)
    return layout
