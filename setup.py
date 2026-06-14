import sys
from cx_Freeze import setup, Executable

# 1. Określenie typu bazy (base)
# Dla aplikacji okienkowych (GUI) na Windowsie chcemy ukryć czarną konsolę tekstową.
base = None
if sys.platform == "win32":
    base = "gui"  # Używamy "gui" dla aplikacji okienkowych, aby nie pokazywała się konsola

# 2. Opcje budowania
build_exe_options = {
    # Włączamy pakiet PyQt6, aby cx_Freeze na pewno go wykrył i spakował
    "packages": ["PyQt6"],
    # Tutaj dodaj pliki, których Twoja aplikacja potrzebuje (np. ikony, bazy danych, pliki .ui)
    # "include_files": ["assets/", "config.json"], 
    "excludes": ["tkinter"],  # Wykluczamy niepotrzebne biblioteki, by zmniejszyć wagę aplikacji
}

# 3. Definicja pliku wykonywalnego
executables = [
    Executable(
        "main.py",                  # Twój główny plik aplikacji
        base=base,
        target_name="ShowControl", # Nazwa pliku .exe (nie dodawaj rozszerzenia .exe, cx_Freeze zrobi to sam)
        icon="ikona.ico"            # Opcjonalnie: ścieżka do ikony aplikacji (musi być format .ico na Win)
    )
]

# 4. Główna konfiguracja setup
setup(
    name="Show-Control",
    version="0.3",
    description="Aplikacja do sterowania multimediami podczas szkolnych uroczystości.",
    options={"build_exe": build_exe_options},
    executables=executables
)