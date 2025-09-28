import re

import markdown
import bleach
from django.utils.safestring import mark_safe

def markdownify(text):
    # Безопасный рендеринг
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'img', 'ul', 'ol', 'li', 'blockquote',
        'code', 'pre', 'strong', 'em', 'br', 'hr'
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
    }
    html = markdown.markdown(text, extensions=['extra', 'codehilite'])
    clean_html = bleach.clean(html, tags=allowed_tags, attributes=allowed_attrs)
    return mark_safe(clean_html)

def convert_rutube_shortcodes(html):
    """
    Заменяет {{ rutube:VIDEO_ID }} на встроенный плеер Rutube
    Пример: {{ rutube:abcdef123456 }} → <iframe ...>
    """
    def replace_rutube(match):
        video_id = match.group(1)
        # Проверяем, что ID состоит из букв/цифр/дефисов/подчёркиваний
        if not re.match(r'^[a-zA-Z0-9_-]+$', video_id):
            return match.group(0)  # не валидный ID — оставляем как есть

        return (
            f'<div class="video-wrapper">'
            f'<iframe src="https://rutube.ru/play/embed/{video_id}" '
            f'frameborder="0" allowfullscreen '
            f'sandbox="allow-same-origin allow-scripts allow-popups" '
            f'width="100%" height="400" loading="lazy"></iframe>'
            f'</div>'
        )

    # Ищем {{ rutube:... }}
    pattern = r'\{\{\s*rutube:\s*([a-zA-Z0-9_-]+)\s*\}\}'
    return re.sub(pattern, replace_rutube, html, flags=re.IGNORECASE)

def markdownify_with_video(text):
    """Рендерит Markdown + Rutube-плееры"""
    if not text:
        return ""

    # 1. Рендерим Markdown
    html = markdown.markdown(text, extensions=['extra'])

    # 2. Добавляем Rutube-плееры ДО bleach (иначе iframe удалят)
    html = convert_rutube_shortcodes(html)

    # 3. Безопасная очистка — разрешаем iframe только для Rutube
    allowed_tags = [
        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'a', 'img', 'ul', 'ol', 'li', 'blockquote',
        'code', 'pre', 'strong', 'em', 'br', 'hr', 'iframe', 'div'
    ]
    allowed_attrs = {
        'a': ['href', 'title'],
        'img': ['src', 'alt', 'title'],
        'iframe': ['src', 'frameborder', 'allowfullscreen', 'sandbox', 'width', 'height', 'loading'],
        'div': ['class'],
    }

    # Разрешаем iframe ТОЛЬКО с rutube.ru
    def allow_rutube_iframe(tag, name, value):
        if tag == 'iframe' and name == 'src':
            return value.startswith('https://rutube.ru/play/embed/')
        return True

    clean_html = bleach.clean(
        html,
        tags=allowed_tags,
        attributes=allowed_attrs,
        protocols=['https'],
        strip=True
    )

    return mark_safe(clean_html)