# blog/utils/upload_paths.py

def _get_location_path_slug(instance):
    """Возвращает путь локации в виде 'rossiya/kazan/...'"""
    if hasattr(instance, 'location') and instance.location:
        return instance.location.get_path_slug()
    elif hasattr(instance, 'post') and instance.post.location:
        return instance.post.location.get_path_slug()
    else:
        return 'uncategorized'

def _get_post_slug(instance):
    """Возвращает slug поста"""
    if hasattr(instance, 'slug'):
        return instance.slug
    elif hasattr(instance, 'post') and instance.post.slug:
        return instance.post.slug
    else:
        return 'untitled'

def cover_upload_to(instance, filename):
    location_path = _get_location_path_slug(instance)
    post_slug = _get_post_slug(instance)
    ext = filename.split('.')[-1]
    return f'post_images/{location_path}/{post_slug}/cover.{ext}'

def gallery_upload_to(instance, filename):
    location_path = _get_location_path_slug(instance)
    post_slug = _get_post_slug(instance)
    ext = filename.split('.')[-1]
    # Сохраняем оригинальное имя файла, но в нужной папке
    # return f'gallery/{location_path}/{post_slug}/{filename}'
    return f'post_images/{location_path}/{post_slug}/gallery.{ext}'
