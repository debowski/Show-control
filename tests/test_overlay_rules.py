"""Precedencja trybu projekcji. Zachowanie v0.7.2 — ADR 0005 zmienia je w fazie 3."""

from showcontrol.domain.overlay_rules import ProjectionPlan, projection_plan


def _plan(**overrides):
    kwargs = {
        "global_overlay_enabled": False,
        "item_overlay_enabled": False,
        "item_overlay_path": None,
        "is_audio": False,
        "overlay_on_audio_enabled": False,
        "global_overlay_path": None,
    }
    kwargs.update(overrides)
    return projection_plan(**kwargs)


def test_media_when_nothing_enabled():
    result = _plan(global_overlay_path="global.png", item_overlay_path="item.png")
    assert result == ProjectionPlan(False, None)


def test_global_overlay_when_enabled():
    result = _plan(global_overlay_enabled=True, global_overlay_path="global.png")
    assert result.show_overlay is True
    assert result.asset_path == "global.png"


def test_global_overlay_enabled_without_asset():
    result = _plan(global_overlay_enabled=True)
    assert result.show_overlay is True
    assert result.asset_path is None


def test_item_overlay_when_enabled():
    result = _plan(item_overlay_enabled=True, item_overlay_path="item.png")
    assert result.show_overlay is True
    assert result.asset_path == "item.png"


def test_item_overlay_without_own_asset_falls_back_to_global():
    result = _plan(item_overlay_enabled=True, global_overlay_path="global.png")
    assert result.show_overlay is True
    assert result.asset_path == "global.png"


def test_item_asset_wins_over_global_asset():
    result = _plan(
        global_overlay_enabled=True,
        item_overlay_enabled=True,
        item_overlay_path="item.png",
        global_overlay_path="global.png",
    )
    assert result.asset_path == "item.png"


def test_item_asset_wins_even_when_item_checkbox_is_off():
    """v0.7.2: asset pozycji wygrywa, gdy overlay włącza F9. Faza 3 to zmieni."""
    result = _plan(
        global_overlay_enabled=True,
        item_overlay_enabled=False,
        item_overlay_path="item.png",
        global_overlay_path="global.png",
    )
    assert result.show_overlay is True
    assert result.asset_path == "item.png"


def test_overlay_on_audio_when_audio_and_enabled():
    result = _plan(
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result.show_overlay is True
    assert result.asset_path == "global.png"


def test_overlay_on_audio_ignored_for_video():
    result = _plan(
        is_audio=False,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(False, None)


def test_overlay_on_audio_combines_with_global_toggle():
    result = _plan(
        global_overlay_enabled=True,
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(True, "global.png")


def test_overlay_on_audio_falls_back_to_item_asset():
    result = _plan(
        item_overlay_enabled=True,
        item_overlay_path="item.png",
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result.asset_path == "item.png"


def test_plan_is_keyword_only():
    try:
        projection_plan(True, False, None, False, False, None)
    except TypeError:
        pass
    else:
        raise AssertionError("projection_plan powinien przyjmować tylko argumenty nazwane")
