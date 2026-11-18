"""Rozszerzenia plików i klasyfikacja mediów. Bez Qt i bez VLC."""

import os

VIDEO_EXTENSIONS = (".mp4", ".mkv")
AUDIO_EXTENSIONS = (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a")
IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".gif")
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS + AUDIO_EXTENSIONS + IMAGE_EXTENSIONS


def has_extension(path, extensions):
    return bool(path and path.lower().endswith(extensions))


def is_audio_file(path):
    return has_extension(path, AUDIO_EXTENSIONS)


def is_image_file(path):
    return has_extension(path, IMAGE_EXTENSIONS)


def is_supported_media_file(path):
    return has_extension(path, MEDIA_EXTENSIONS)


def find_media_paths(path):
    if os.path.isfile(path):
        return [path] if is_supported_media_file(path) else []

    if not os.path.isdir(path):
        return []

    paths = []
    for root, _, files in os.walk(path):
        for filename in files:
            media_path = os.path.join(root, filename)
            if is_supported_media_file(media_path):
                paths.append(media_path)
    return paths
