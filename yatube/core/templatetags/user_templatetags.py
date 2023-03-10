from django import template

register = template.Library()

@register.simple_tag
def update_chat_day(value):
    """Обновляет день в чате."""
    return value