"""
ЧистеФото — AI-функції.

Уся робота з AI живе тут, окремо від інтерфейсу (app.py).
Головна функція: remove_background() із заняття 7 — видаляє фон із фото.
Працює локально (бібліотека rembg), API-ключ не потрібен.
"""

import io

from PIL import Image
from rembg import new_session, remove

_session = None


def _get_session():
    global _session
    if _session is None:
        _session = new_session("u2netp")
    return _session


def remove_background(image_bytes):
    """Прибирає фон із фото.

    Вхід:      вміст файлу (bytes) — JPG або PNG.
    Обробка:   rembg вирізає предмет і робить фон прозорим.
    Результат: Image у режимі RGBA (предмет + прозорий фон).
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return remove(image, session=_get_session())


def on_white_background(cutout):
    """Кладе вирізаний предмет на білий фон — формат фото для оголошень."""
    white = Image.new("RGB", cutout.size, "white")
    white.paste(cutout, mask=cutout.split()[3])  # альфа-канал як маска
    return white


def to_png_bytes(image):
    """Перетворює зображення на байти PNG (для кнопки «Завантажити»)."""
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else "test.jpg"
    with open(path, "rb") as f:
        result = on_white_background(remove_background(f.read()))
    result.save("test_result.png")
    print("Готово: test_result.png")
