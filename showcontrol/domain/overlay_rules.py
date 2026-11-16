"""Precedencja trybu projekcji — czysta funkcja, bez Qt i bez VLC."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectionPlan:
    """Wynik rozstrzygnięcia: czy pokazać overlay i który asset załadować."""

    show_overlay: bool
    asset_path: str | None


def projection_plan(*, global_overlay_enabled, item_overlay_enabled,
                    item_overlay_path, is_audio, overlay_on_audio_enabled,
                    global_overlay_path):
    """Rozstrzyga tryb projekcji dla bieżącej pozycji.

    Odwzorowuje zachowanie `v0.7.2`: warunki są alternatywą (F9 tylko włącza
    overlay globalny), a asset pozycji wygrywa z globalnym. ADR 0005 zmienia
    semantykę F9 w fazie 3 — wtedy ten test się zmieni.
    """
    show_overlay = (
        global_overlay_enabled
        or item_overlay_enabled
        or (is_audio and overlay_on_audio_enabled)
    )
    if not show_overlay:
        return ProjectionPlan(False, None)
    return ProjectionPlan(True, item_overlay_path or global_overlay_path)
