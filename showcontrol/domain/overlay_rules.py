"""Precedencja trybu projekcji — czysta funkcja, bez Qt i bez VLC."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ProjectionPlan:
    """Wynik rozstrzygnięcia: czy pokazać overlay i który asset załadować."""

    show_overlay: bool
    asset_path: str | None


def projection_plan(
    *,
    force_overlay_enabled,
    item_overlay_enabled,
    item_overlay_path,
    is_audio,
    overlay_on_audio_enabled,
    global_overlay_path,
):
    """Rozstrzyga tryb projekcji według priorytetu z ADR 0005.

    F9 (wymuszony overlay) wygrywa z overlaya pozycji i z F10. Overlay pozycji
    liczy się tylko z własnym assetem; bez assetu checkbox jest nieaktywny.
    F10 działa wyłącznie przy wyłączonym F9.
    """
    if force_overlay_enabled and global_overlay_path:
        return ProjectionPlan(True, global_overlay_path)

    if item_overlay_enabled and item_overlay_path:
        return ProjectionPlan(True, item_overlay_path)

    if is_audio and overlay_on_audio_enabled:
        return ProjectionPlan(True, global_overlay_path)

    return ProjectionPlan(False, None)
