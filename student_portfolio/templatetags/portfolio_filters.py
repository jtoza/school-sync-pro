from django import template

register = template.Library()

@register.filter
def split(value, delimiter=','):
    """Split a string by delimiter and return as list"""
    if value:
        return [item.strip() for item in value.split(delimiter)]
    return []

@register.filter
def get_first_chars(value, num_chars=2):
    """Get first characters of first and last name"""
    if value and hasattr(value, 'first_name') and hasattr(value, 'last_name'):
        first_char = value.first_name[0] if value.first_name else ''
        last_char = value.last_name[0] if value.last_name else ''
        return f"{first_char}{last_char}"
    return "??"