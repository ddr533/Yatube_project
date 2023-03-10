from django import template

register = template.Library()

@register.simple_tag
def update_chat_day(value):
    """Возвращает переданное значение в шаблон.
    Используется в чате для получения номера дня
    текущего сообщения.
    """
    return value