"""Lista playlisty: adapter Qt na `PlaylistStore`, widok, proxy i delegate."""

import os

from PyQt6.QtCore import Qt, QAbstractListModel, QModelIndex, QUrl, QSortFilterProxyModel, QRect, QEvent
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import QListView, QFileDialog, QStyledItemDelegate

from showcontrol.domain.media import find_media_paths
from showcontrol.domain.playlist import PlaylistStore
from showcontrol.ui.i18n import DEFAULT_LANGUAGE, get_t, overlay_item_dialog_filter
from showcontrol.ui.theme import theme_color


def _translate(widget, key, **kwargs):
    """Tłumaczenie z okna operatora, z bezpiecznym fallbackiem dla testów."""
    if widget is not None and hasattr(widget, "get_t"):
        return widget.get_t(key, **kwargs)
    return get_t(DEFAULT_LANGUAGE, key, **kwargs)


class PlaylistModel(QAbstractListModel):
    """Cienki adapter Qt: dane i operacje na wierszach należą do PlaylistStore."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._store = PlaylistStore()
        self._playing_row = -1

    @property
    def store(self):
        return self._store

    @property
    def playing_row(self):
        return self._playing_row

    def entries(self):
        return self._store.rows()

    def rowCount(self, parent=QModelIndex()):
        return self._store.row_count()

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        row = index.row()
        entry = self._store.entry_at(row)

        if role == Qt.ItemDataRole.DisplayRole:
            return entry.filename
        elif role == Qt.ItemDataRole.UserRole:
            return entry.path
        elif role == Qt.ItemDataRole.UserRole + 1:
            return entry.overlay_path
        elif role == Qt.ItemDataRole.ToolTipRole:
            tooltip = entry.path
            if entry.overlay_path:
                tooltip += " " + _translate(
                    self.parent(),
                    "overlay_item_tooltip",
                    name=os.path.basename(entry.overlay_path),
                )
            elif entry.overlay:
                tooltip += " " + _translate(self.parent(), "overlay_global_tooltip")
            return tooltip
        elif role == Qt.ItemDataRole.CheckStateRole:
            if not entry.overlay_path:
                return None
            return Qt.CheckState.Checked if entry.overlay else Qt.CheckState.Unchecked
        elif role == Qt.ItemDataRole.BackgroundRole:
            if row == self.playing_row:
                return QColor(theme_color("list_play"))
        elif role == Qt.ItemDataRole.FontRole:
            if row == self.playing_row:
                return QFont("Segoe UI", 10, QFont.Weight.Bold)

        return None

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        if not index.isValid():
            return False
        if role == Qt.ItemDataRole.CheckStateRole:
            if not self._store.overlay_path_for_row(index.row()):
                return False
            checked = (value == Qt.CheckState.Checked) if isinstance(value, Qt.CheckState) else bool(value)
            self._store.set_overlay(index.row(), checked)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def flags(self, index):
        default_flags = super().flags(index)
        if index.isValid():
            flags = (
                default_flags | Qt.ItemFlag.ItemIsDragEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
            )
            if self._store.overlay_path_for_row(index.row()):
                flags |= Qt.ItemFlag.ItemIsUserCheckable
            return flags
        return default_flags | Qt.ItemFlag.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.DropAction.CopyAction | Qt.DropAction.MoveAction

    def mimeTypes(self):
        return ["text/uri-list", "application/x-qabstractitemmodeldatalist"]

    def mimeData(self, indexes):
        mime_data = super().mimeData(indexes)
        rows = [index.row() for index in indexes if index.isValid()]
        mime_data.setUrls([QUrl.fromLocalFile(self._store.path_at(row)) for row in rows])
        return mime_data

    def dropMimeData(self, data, action, row, _column, parent):
        if action == Qt.DropAction.IgnoreAction:
            return True

        target_row = row if row != -1 else self.rowCount()

        if data.hasUrls():
            paths = []
            for url in data.urls():
                paths.extend(find_media_paths(url.toLocalFile()))
            return self.add_files(paths, target_row, parent)

        return False

    def insertRows(self, row, count, parent=QModelIndex()):
        self.beginInsertRows(parent, row, row + count - 1)
        self._store.insert_blanks(row, count)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent=QModelIndex()):
        self.beginRemoveRows(parent, row, row + count - 1)
        self._store.remove(row, count)
        self.endRemoveRows()
        return True

    def moveRows(self, sourceParent, sourceRow, count, destinationParent, destinationChild):
        if not self._store.can_move(sourceRow, count, destinationChild):
            return False

        self.beginMoveRows(sourceParent, sourceRow, sourceRow + count - 1, destinationParent, destinationChild)
        self._store.move(sourceRow, count, destinationChild)
        self.endMoveRows()
        return True

    def add_files(self, file_paths, row=None, parent=QModelIndex()):
        file_paths = [path for path in file_paths if path]
        if not file_paths:
            return False

        insert_row = self.rowCount() if row is None or row == -1 else row
        self.beginInsertRows(parent, insert_row, insert_row + len(file_paths) - 1)
        self._store.add(file_paths, insert_row)
        self.endInsertRows()

        self.dataChanged.emit(self.index(insert_row, 0), self.index(insert_row + len(file_paths) - 1, 0))
        return True

    def clear(self):
        self.beginResetModel()
        self._store.clear()
        self.endResetModel()

    def replace_entries(self, entries):
        """Podmienia całą playlistę jednym resetem modelu."""
        self.beginResetModel()
        self._store.replace_entries(entries)
        self.endResetModel()

    def overlay_for_row(self, row):
        """Zwraca True jeśli dany wiersz ma ustawioną nakładkę."""
        return self._store.overlay_for_row(row)

    def overlay_path_for_row(self, row):
        """Zwraca ścieżkę do nakładki dla danego wiersza lub None."""
        return self._store.overlay_path_for_row(row)

    def set_overlay_path(self, row, path):
        """Ustawia indywidualną nakładkę dla wiersza."""
        self._store.set_overlay_path(row, path)
        if 0 <= row < self.rowCount():
            idx = self.index(row, 0)
            self.dataChanged.emit(
                idx, idx, [Qt.ItemDataRole.ToolTipRole, Qt.ItemDataRole.CheckStateRole, Qt.ItemDataRole.UserRole + 1]
            )

    def set_overlay_state(self, row, overlay, overlay_path):
        """Ustawia flagę i ścieżkę bez emitowania sygnału — patrz refresh_rows()."""
        self._store.set_overlay_state(row, overlay, overlay_path)

    def refresh_rows(self, top, bottom):
        if 0 <= top <= bottom:
            self.dataChanged.emit(self.index(top, 0), self.index(bottom, 0))

    def set_playing_row(self, row):
        """Wskaźnik do narysowania; właścicielem stanu jest sesja."""
        old_row = self._playing_row
        self._playing_row = row

        # Podświetlenie to wyłącznie wygląd. Bez ról `dataChanged` znaczy
        # „zmieniło się wszystko" i okno przelicza tryb projekcji w trakcie
        # startu odtwarzania — drugie `apply` obchodzi kurtynę i overlay
        # błyska przed jej zasłonięciem.
        roles = [Qt.ItemDataRole.BackgroundRole, Qt.ItemDataRole.FontRole]
        if 0 <= old_row < self.rowCount():
            self.dataChanged.emit(self.index(old_row, 0), self.index(old_row, 0), roles)
        if 0 <= row < self.rowCount():
            self.dataChanged.emit(self.index(row, 0), self.index(row, 0), roles)


class PlaylistView(QListView):
    """QListView z prawidłową obsługą wewnętrznego przenoszenia oraz drag & drop z zewnątrz."""

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls() or event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        # Jeśli przeciągamy element wewnątrz tego samego widoku
        if event.source() == self:
            # Pozwalamy Qt na standardowe obsłużenie MoveAction przez model/proxy
            super().dropEvent(event)
        elif event.mimeData().hasUrls():
            # Elementy z zewnątrz (np. z Eksploratora) wymuszają CopyAction
            event.setDropAction(Qt.DropAction.CopyAction)
            event.accept()
            model = self.model()
            if model:
                pos = event.position().toPoint()
                idx = self.indexAt(pos)
                row = idx.row() if idx.isValid() else -1
                model.dropMimeData(event.mimeData(), Qt.DropAction.CopyAction, row, 0, idx.parent())
        else:
            super().dropEvent(event)


class PlaylistFilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)

    def filterAcceptsRow(self, source_row, source_parent):
        # Akceptuj wszystko jeśli filtr pusty
        if not self.filterRegularExpression().pattern():
            return True

        model = self.sourceModel()
        index = model.index(source_row, 0, source_parent)
        filename = model.data(index, Qt.ItemDataRole.DisplayRole)

        if filename:
            # match instead of indexof
            return self.filterRegularExpression().match(filename).hasMatch()
        return False

    def moveRows(self, source_parent, source_row, count, destination_parent, destination_child):
        """Przenosi wiersze w modelu źródłowym — QListView używa tego przy DnD.

        Bez tej metody Qt nie umie przenieść wiersza przez proxy i cofa się do
        `dropMimeData`, po czym usuwa przeciągnięty wiersz jako „przeniesiony".
        """
        model = self.sourceModel()
        source_parent = self.mapToSource(source_parent)
        destination_parent = self.mapToSource(destination_parent)

        source_start = self.mapToSource(self.index(source_row, 0)).row()
        if destination_child >= self.rowCount():
            source_destination = model.rowCount()
        else:
            source_destination = self.mapToSource(self.index(destination_child, 0)).row()

        return model.moveRows(source_parent, source_start, count, destination_parent, source_destination)


class PlaylistItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.btn_size = 24
        self.margin = 4

    def paint(self, painter, option, index):
        super().paint(painter, option, index)

        overlay_path = index.data(Qt.ItemDataRole.UserRole + 1)

        # 1. Obliczamy pozycje przycisków wyrównane do prawej
        rect = option.rect
        right_edge = rect.right() - self.margin

        # Przycisk ✖ (reset) - widoczny tylko gdy jest przypisana nakładka
        reset_rect = QRect()
        if overlay_path:
            reset_rect = QRect(
                right_edge - self.btn_size,
                rect.top() + (rect.height() - self.btn_size) // 2,
                self.btn_size,
                self.btn_size,
            )
            right_edge -= self.btn_size + self.margin

        # Przycisk 📁 (wybór nakładki) - zawsze widoczny
        folder_rect = QRect(
            right_edge - self.btn_size, rect.top() + (rect.height() - self.btn_size) // 2, self.btn_size, self.btn_size
        )

        # 2. Rysowanie
        painter.save()

        # Rysowanie ikony 📁
        # Tło
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(theme_color("bg_btn")))
        painter.drawRoundedRect(folder_rect, 3, 3)
        # Tekst
        painter.setPen(QColor(theme_color("text")))
        painter.drawText(folder_rect, Qt.AlignmentFlag.AlignCenter, "📁")

        # Rysowanie ikony ✖ jeśli potrzebna
        if overlay_path:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(theme_color("stop")))
            painter.drawRoundedRect(reset_rect, 3, 3)
            painter.setPen(QColor(theme_color("text")))
            painter.drawText(reset_rect, Qt.AlignmentFlag.AlignCenter, "✖")

        painter.restore()

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()

            overlay_path = index.data(Qt.ItemDataRole.UserRole + 1)
            rect = option.rect
            right_edge = rect.right() - self.margin

            reset_rect = QRect()
            if overlay_path:
                reset_rect = QRect(
                    right_edge - self.btn_size,
                    rect.top() + (rect.height() - self.btn_size) // 2,
                    self.btn_size,
                    self.btn_size,
                )
                right_edge -= self.btn_size + self.margin

            folder_rect = QRect(
                right_edge - self.btn_size,
                rect.top() + (rect.height() - self.btn_size) // 2,
                self.btn_size,
                self.btn_size,
            )

            # Sprawdź kliknięcie ✖
            if overlay_path and reset_rect.contains(pos):
                if hasattr(model, "sourceModel"):
                    source_idx = model.mapToSource(index)
                    model.sourceModel().set_overlay_path(source_idx.row(), None)
                else:
                    model.set_overlay_path(index.row(), None)
                return True

            # Sprawdź kliknięcie 📁
            if folder_rect.contains(pos):
                parent_widget = option.widget
                window = parent_widget.window() if parent_widget else None
                dialog_title = _translate(window, "select_overlay_dialog")
                filter_text = overlay_item_dialog_filter(getattr(window, "language", DEFAULT_LANGUAGE))
                path, _ = QFileDialog.getOpenFileName(parent_widget, dialog_title, "", filter_text)
                if path:
                    if hasattr(model, "sourceModel"):
                        source_idx = model.mapToSource(index)
                        model.sourceModel().set_overlay_path(source_idx.row(), path)
                    else:
                        model.set_overlay_path(index.row(), path)
                return True

        return super().editorEvent(event, model, option, index)
