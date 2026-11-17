"""Precedencja trybu projekcji według ADR 0005. Bez Qt i VLC."""

from showcontrol.domain.overlay_rules import ProjectionPlan, projection_plan


def _plan(**overrides):
    kwargs = {
        "force_overlay_enabled": False,
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


def test_force_overlay_shows_global_asset():
    result = _plan(force_overlay_enabled=True, global_overlay_path="global.png")
    assert result == ProjectionPlan(True, "global.png")


def test_force_overlay_beats_item_overlay():
    result = _plan(
        force_overlay_enabled=True,
        global_overlay_path="global.png",
        item_overlay_enabled=True,
        item_overlay_path="item.png",
    )
    assert result == ProjectionPlan(True, "global.png")


def test_force_overlay_without_asset_is_not_forced():
    result = _plan(force_overlay_enabled=True)
    assert result == ProjectionPlan(False, None)


def test_item_overlay_needs_its_own_asset():
    result = _plan(item_overlay_enabled=True, item_overlay_path="item.png")
    assert result == ProjectionPlan(True, "item.png")


def test_item_overlay_without_own_asset_does_not_fall_back_to_global():
    result = _plan(item_overlay_enabled=True, global_overlay_path="global.png")
    assert result == ProjectionPlan(False, None)


def test_item_overlay_is_ignored_when_checkbox_is_off():
    result = _plan(
        item_overlay_enabled=False,
        item_overlay_path="item.png",
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(False, None)


def test_overlay_on_audio_uses_global_asset():
    result = _plan(
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(True, "global.png")


def test_overlay_on_audio_without_asset_does_not_enter_overlay_mode():
    result = _plan(is_audio=True, overlay_on_audio_enabled=True)
    assert result == ProjectionPlan(False, None)


def test_overlay_on_audio_is_ignored_for_video():
    result = _plan(
        is_audio=False,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(False, None)


def test_force_overlay_beats_overlay_on_audio():
    result = _plan(
        force_overlay_enabled=True,
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(True, "global.png")


def test_item_overlay_beats_overlay_on_audio():
    result = _plan(
        item_overlay_enabled=True,
        item_overlay_path="item.png",
        is_audio=True,
        overlay_on_audio_enabled=True,
        global_overlay_path="global.png",
    )
    assert result == ProjectionPlan(True, "item.png")


def test_plan_is_keyword_only():
    try:
        projection_plan(True, False, None, False, False, None)
    except TypeError:
        pass
    else:
        raise AssertionError("projection_plan powinien przyjmować tylko argumenty nazwane")
