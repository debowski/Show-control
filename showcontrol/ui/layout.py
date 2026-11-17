"""Układ okna operatora: trzy panele zamiast jednego ``init_ui``.

Panel górny odpowiada za zarządzanie playlistą i wyszukiwanie, panel środkowy
za listę i jej kolejność, a panel dolny za transport oraz ustawienia. Funkcje
przyjmują okno (``window``) i tworzą na nim atrybuty widżetów — dokładnie te,
których oczekują metody ``MainWindow``.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from showcontrol.ui.i18n import LANGUAGE_KEYS, LANGUAGE_NAMES
from showcontrol.ui.peak_meter import StereoPeakMeter
from showcontrol.ui.playlist_view import PlaylistFilterProxyModel, PlaylistItemDelegate, PlaylistView
from showcontrol.ui.theme import THEME_KEYS, THEMES


def build_main_layout(window):
    """Buduje cały układ okna i podłącza sygnały do metod ``window``."""
    central = QWidget()
    window.setCentralWidget(central)
    root = QVBoxLayout(central)
    root.setContentsMargins(15, 15, 15, 15)
    root.setSpacing(10)

    _build_top_panel(window, root)
    _build_playlist_panel(window, root)
    _build_control_panel(window, root)


def _build_top_panel(window, root):
    """Górny pasek zarządzania oraz pole wyszukiwania."""
    top_bar = QHBoxLayout()
    mgmt_left = QHBoxLayout()
    window.add_btn = QPushButton()
    window.add_btn.setObjectName("AddFilesButton")
    window.add_btn.clicked.connect(window.add_files)
    window.remove_btn = QPushButton()
    window.remove_btn.setObjectName("RemoveFileButton")
    window.remove_btn.clicked.connect(window.remove_file)
    mgmt_left.addWidget(window.add_btn)
    mgmt_left.addWidget(window.remove_btn)

    mgmt_right = QHBoxLayout()
    window.load_proj_btn = QPushButton()
    window.load_proj_btn.setObjectName("LoadProjectButton")
    window.load_proj_btn.clicked.connect(window.load_project)
    window.save_proj_btn = QPushButton()
    window.save_proj_btn.setObjectName("SaveProjectButton")
    window.save_proj_btn.clicked.connect(window.save_project)
    mgmt_right.addWidget(window.load_proj_btn)
    mgmt_right.addWidget(window.save_proj_btn)

    top_bar.addLayout(mgmt_left)
    top_bar.addStretch()

    window.overlay_btn = QPushButton()
    window.overlay_btn.setObjectName("SelectOverlayButton")
    window.overlay_btn.clicked.connect(window.select_overlay)

    window.clear_overlay_btn = QPushButton()
    window.clear_overlay_btn.setObjectName("ClearOverlayButton")
    window.clear_overlay_btn.clicked.connect(window.clear_overlay)

    window.overlay_status_label = QLabel()
    window.overlay_status_label.setObjectName("OverlayStatusLabel")

    window.window_btn = QPushButton()
    window.window_btn.setObjectName("HideBtn")
    window.window_btn.clicked.connect(window.toggle_projection_window)

    mgmt_center = QHBoxLayout()
    mgmt_center.addWidget(window.overlay_btn)
    mgmt_center.addWidget(window.clear_overlay_btn)
    mgmt_center.addWidget(window.overlay_status_label)
    mgmt_center.addWidget(window.window_btn)
    top_bar.addLayout(mgmt_center)

    top_bar.addStretch()
    top_bar.addLayout(mgmt_right)
    root.addLayout(top_bar)

    search_layout = QHBoxLayout()
    window.search_input = QLineEdit()
    window.search_input.setObjectName("SearchInput")
    window.search_input.setPlaceholderText("")
    window.search_input.setClearButtonEnabled(True)
    window.search_input.textChanged.connect(window.filter_playlist)
    search_layout.addWidget(window.search_input)
    root.addLayout(search_layout)


def _build_playlist_panel(window, root):
    """Lista plików, delegat, przeciąganie i przyciski kolejności."""
    window.proxy_model = PlaylistFilterProxyModel(window)
    window.proxy_model.setSourceModel(window.playlist_model)
    # Na żywo aktualizuj tryb projekcji gdy operator zmieni checkbox nakładki
    window.playlist_model.dataChanged.connect(window._on_playlist_overlay_changed)

    window.playlist = PlaylistView(window)
    window.playlist.setModel(window.proxy_model)
    window.playlist.setItemDelegate(PlaylistItemDelegate(window.playlist))
    window.playlist.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    window.playlist.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    window.playlist.setAlternatingRowColors(True)
    window.playlist.viewport().setMouseTracking(True)

    # DragDrop (nie InternalMove) pozwala akceptować pliki z zewnątrz (Eksplorator)
    window.playlist.setDragEnabled(True)
    window.playlist.setAcceptDrops(True)
    window.playlist.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
    window.playlist.setDropIndicatorShown(True)
    window.playlist.setDefaultDropAction(Qt.DropAction.MoveAction)

    window.playlist.doubleClicked.connect(lambda idx: window.play_media())

    window.move_up_btn = QPushButton("▲")
    window.move_up_btn.setObjectName("MoveBtn")
    window.move_up_btn.setFixedSize(28, 28)
    window.move_up_btn.clicked.connect(window.move_item_up)

    window.move_down_btn = QPushButton("▼")
    window.move_down_btn.setObjectName("MoveBtn")
    window.move_down_btn.setFixedSize(28, 28)
    window.move_down_btn.clicked.connect(window.move_item_down)

    move_btn_layout = QVBoxLayout()
    move_btn_layout.setContentsMargins(0, 0, 0, 0)
    move_btn_layout.setSpacing(4)
    move_btn_layout.addWidget(window.move_up_btn)
    move_btn_layout.addWidget(window.move_down_btn)
    move_btn_layout.addStretch()

    playlist_row = QHBoxLayout()
    playlist_row.setSpacing(6)
    playlist_row.addWidget(window.playlist, stretch=1)
    playlist_row.addLayout(move_btn_layout)
    root.addLayout(playlist_row, stretch=1)


def _build_control_panel(window, root):
    """Transport oraz dolny panel z efektami, dźwiękiem i ustawieniami."""
    transport_frame = QGroupBox()
    transport_frame.setObjectName("TransportGroup")
    window.transport_group = transport_frame
    trans_layout = QVBoxLayout(transport_frame)
    window.progress_slider = QSlider(Qt.Orientation.Horizontal)
    window.progress_slider.setRange(0, 1000)
    window.progress_slider.setFixedHeight(25)
    window.progress_slider.sliderMoved.connect(window.session.set_position)
    window.progress_slider.sliderPressed.connect(window.session.begin_seek)
    window.progress_slider.sliderReleased.connect(lambda: window.session.end_seek(window.progress_slider.value()))

    window.time_label = QLabel(window.get_t("empty_time_label"))
    window.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.time_label.setObjectName("TimeLabel")

    trans_layout.addWidget(window.progress_slider)
    trans_layout.addWidget(window.time_label)

    btns_grid = QHBoxLayout()
    btns_grid.setSpacing(5)
    window.prev_btn = QPushButton()
    window.prev_btn.setObjectName("TransportBtn")
    window.prev_btn.clicked.connect(window.play_previous_file)

    window.play_btn = QPushButton()
    window.play_btn.setObjectName("PlayBtn")
    window.play_btn.clicked.connect(window.play_media)

    window.pause_btn = QPushButton()
    window.pause_btn.setObjectName("TransportBtn")
    window.pause_btn.clicked.connect(window.toggle_play_pause)

    window.stop_btn = QPushButton()
    window.stop_btn.setObjectName("StopBtn")
    window.stop_btn.clicked.connect(window.stop_media)

    window.next_btn = QPushButton()
    window.next_btn.setObjectName("TransportBtn")
    window.next_btn.clicked.connect(window.play_next_file)

    for btn in (window.prev_btn, window.play_btn, window.pause_btn, window.stop_btn, window.next_btn):
        btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        btns_grid.addWidget(btn)
    trans_layout.addLayout(btns_grid)
    root.addWidget(transport_frame)

    _build_bottom_panel(window, root)


def _build_bottom_panel(window, root):
    bottom_panel = QHBoxLayout()
    view_group = QGroupBox()
    view_group.setObjectName("ViewEffectsGroup")
    window.view_group = view_group
    view_layout = QVBoxLayout(view_group)
    window.fade_btn = QPushButton()
    window.fade_btn.setObjectName("FadeBtn")
    window.fade_btn.clicked.connect(window.fade_out)
    window.fullscreen_btn = QPushButton()
    window.fullscreen_btn.clicked.connect(window.toggle_projection_fullscreen)
    window.force_overlay_btn = QPushButton()
    window.force_overlay_btn.setCheckable(True)
    window.force_overlay_btn.setObjectName("TransportBtn")
    window.force_overlay_btn.toggled.connect(window.toggle_overlay)
    view_layout.addWidget(window.fade_btn)
    view_layout.addWidget(window.fullscreen_btn)
    view_layout.addWidget(window.force_overlay_btn)

    audio_group = QGroupBox()
    audio_group.setObjectName("ControlGroup")
    window.audio_group = audio_group
    audio_main_layout = QHBoxLayout(audio_group)
    _build_meter(window, audio_main_layout)
    _build_volume(window, audio_main_layout)
    _build_brightness(window, audio_main_layout)
    _build_fade_speed(window, audio_main_layout)

    bottom_panel.addWidget(view_group, stretch=1)
    bottom_panel.addWidget(audio_group, stretch=1)
    bottom_panel.addWidget(_build_settings(window), stretch=1)
    root.addLayout(bottom_panel)

    window.setup_button_feedback(
        window.add_btn,
        window.remove_btn,
        window.load_proj_btn,
        window.save_proj_btn,
        window.overlay_btn,
        window.window_btn,
        window.prev_btn,
        window.play_btn,
        window.pause_btn,
        window.stop_btn,
        window.next_btn,
        window.fade_btn,
        window.fullscreen_btn,
        window.force_overlay_btn,
    )
    window.init_shortcuts()
    # Apply translations at the end of UI init so all widgets exist
    window.apply_translations()


def _build_meter(window, audio_main_layout):
    meter_layout = QVBoxLayout()
    meter_title = QLabel()
    meter_title.setObjectName("MeterTitle")
    window.meter_title = meter_title
    meter_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.meter_peak_label = QLabel("-∞ dBFS")
    window.meter_peak_label.setObjectName("PeakLabel")
    window.meter_peak_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.peak_meter = StereoPeakMeter()
    window.peak_meter.peak_changed.connect(window._on_peak_changed)
    meter_layout.addWidget(meter_title)
    meter_layout.addWidget(window.meter_peak_label)
    meter_layout.addWidget(window.peak_meter, alignment=Qt.AlignmentFlag.AlignHCenter)

    audio_main_layout.addStretch()
    audio_main_layout.addLayout(meter_layout)
    audio_main_layout.addSpacing(12)


def _build_volume(window, audio_main_layout):
    vol_slider_layout = QVBoxLayout()
    vol_title = QLabel()
    vol_title.setObjectName("VolumeTitle")
    window.volume_title = vol_title
    vol_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.vol_label = QLabel("100%")
    window.vol_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.volume_slider = QSlider(Qt.Orientation.Vertical)
    window.volume_slider.setRange(0, 100)
    window.volume_slider.setValue(100)
    window.volume_slider.valueChanged.connect(window.set_volume)
    vol_slider_layout.addWidget(vol_title)
    vol_slider_layout.addWidget(window.vol_label)
    vol_slider_layout.addWidget(window.volume_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

    audio_main_layout.addLayout(vol_slider_layout)
    audio_main_layout.addSpacing(12)


def _build_brightness(window, audio_main_layout):
    bri_slider_layout = QVBoxLayout()
    bri_title = QLabel()
    bri_title.setObjectName("BrightnessTitle")
    window.brightness_title = bri_title
    bri_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.bri_label = QLabel("100%")
    window.bri_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.brightness_slider = QSlider(Qt.Orientation.Vertical)
    window.brightness_slider.setRange(0, 100)
    window.brightness_slider.setValue(100)
    window.brightness_slider.valueChanged.connect(window.set_brightness)
    bri_slider_layout.addWidget(bri_title)
    bri_slider_layout.addWidget(window.bri_label)
    bri_slider_layout.addWidget(window.brightness_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

    audio_main_layout.addLayout(bri_slider_layout)
    audio_main_layout.addSpacing(12)


def _build_fade_speed(window, audio_main_layout):
    fade_slider_layout = QVBoxLayout()
    fade_title = QLabel()
    fade_title.setObjectName("FadeTitle")
    window.fade_title = fade_title
    fade_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.fade_speed_label = QLabel("0.8s")
    window.fade_speed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    window.fade_speed_slider = QSlider(Qt.Orientation.Vertical)
    # Zakres 0–10 (= 0.0s–1.0s, skalujemy /10 → czyli 10 = 1.0s)
    window.fade_speed_slider.setRange(0, 10)
    # Podłączamy przed setValue, żeby etykieta od razu pokazała wartość domyślną
    window.fade_speed_slider.valueChanged.connect(window._on_fade_speed_changed)
    window.fade_speed_slider.setValue(8)  # domyślnie 0.8s
    fade_slider_layout.addWidget(fade_title)
    fade_slider_layout.addWidget(window.fade_speed_label)
    fade_slider_layout.addWidget(window.fade_speed_slider, alignment=Qt.AlignmentFlag.AlignHCenter)

    audio_main_layout.addLayout(fade_slider_layout)
    audio_main_layout.addSpacing(12)
    audio_main_layout.addStretch()


def _build_settings(window):
    settings_group = QGroupBox()
    settings_group.setObjectName("SettingsGroup")
    window.settings_group = settings_group
    set_layout = QVBoxLayout(settings_group)
    # Language selector will be added here; default set from settings
    window.language = window.settings.get_language()

    window.autoplay_checkbox = QCheckBox()
    # we'll set texts after building UI via apply_translations()
    window.autoplay_checkbox.stateChanged.connect(window._on_autoplay_changed)

    image_speed_layout = QHBoxLayout()
    image_speed_title = QLabel()
    image_speed_title.setObjectName("ImageSpeedTitle")
    window.image_speed_title = image_speed_title
    window.image_switch_delay = QSpinBox()
    window.image_switch_delay.setRange(1, 60)
    window.image_switch_delay.setValue(5)
    window.image_switch_delay.setSuffix(" s")
    window.image_switch_delay.setFixedWidth(100)
    image_speed_layout.addWidget(image_speed_title)
    image_speed_layout.addStretch()
    image_speed_layout.addWidget(window.image_switch_delay)

    window.remote_checkbox = QCheckBox()
    window.remote_checkbox.setChecked(True)
    window.remote_checkbox.stateChanged.connect(lambda: window.update_shortcuts())
    window.overlay_on_audio_checkbox = QCheckBox()
    window.overlay_on_audio_checkbox.setChecked(False)
    window.overlay_on_audio_checkbox.stateChanged.connect(lambda: window.update_overlay_visibility())

    # --- Theme selector ---
    theme_row = QHBoxLayout()
    window.theme_label = QLabel()
    window.theme_combo = QComboBox()
    for key in THEME_KEYS:
        window.theme_combo.addItem(THEMES[key]["name"], key)
    saved_theme = window.settings.get_theme()
    saved_idx = THEME_KEYS.index(saved_theme) if saved_theme in THEME_KEYS else 0
    window.theme_combo.setCurrentIndex(saved_idx)
    window.theme_combo.currentIndexChanged.connect(window._on_theme_changed)
    theme_row.addWidget(window.theme_label)
    theme_row.addWidget(window.theme_combo, stretch=1)

    set_layout.addWidget(window.autoplay_checkbox)
    set_layout.addLayout(image_speed_layout)
    set_layout.addWidget(window.remote_checkbox)
    set_layout.addWidget(window.overlay_on_audio_checkbox)
    set_layout.addLayout(theme_row)

    # --- Language selector ---
    lang_row = QHBoxLayout()
    window.lang_label = QLabel()
    window.lang_label.setObjectName("LanguageLabel")
    window.lang_combo = QComboBox()
    window.lang_combo.setObjectName("LanguageCombo")
    # Adding a language is a data change in ui/i18n.py, not code here.
    for key in LANGUAGE_KEYS:
        window.lang_combo.addItem(LANGUAGE_NAMES.get(key, key), key)
    idx = window.lang_combo.findData(window.language)
    window.lang_combo.setCurrentIndex(idx if idx >= 0 else 0)
    window.lang_combo.currentIndexChanged.connect(window._on_language_changed)
    lang_row.addWidget(window.lang_label)
    lang_row.addWidget(window.lang_combo, stretch=1)
    set_layout.addLayout(lang_row)
    set_layout.addStretch()
    return settings_group
