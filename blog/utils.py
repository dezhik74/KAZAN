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
