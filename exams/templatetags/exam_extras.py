from django import template

register = template.Library()

@register.filter
def round(value, decimal_places=0):
    try:
        return round(float(value), decimal_places)
    except (ValueError, TypeError):
        return value

@register.filter
def percentage(value, decimal_places=0):
    try:
        return f"{round(float(value) * 100, decimal_places)}%"
    except (ValueError, TypeError):
        return value
