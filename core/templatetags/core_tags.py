"""
Template tags for core scoring functionality
"""

from django import template
from django.utils.html import format_html

register = template.Library()

@register.filter
def mul(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def total_marks(questions):
    """Calculate total marks from questions"""
    try:
        return sum(question.max_marks for question in questions)
    except (AttributeError, TypeError):
        return 0

@register.filter
def question_types_count(questions):
    """Count unique question types"""
    try:
        return len(set(question.question_type for question in questions))
    except (AttributeError, TypeError):
        return 0

@register.filter
def custom_settings_count(questions):
    """Count questions with custom settings"""
    try:
        return sum(1 for question in questions 
                  if question.custom_full_threshold or 
                  question.custom_partial_threshold or 
                  question.custom_minimum_threshold)
    except (AttributeError, TypeError):
        return 0

@register.simple_tag
def get_scoring_config_color(threshold_type):
    """Get color for threshold type"""
    colors = {
        'full': '#28a745',
        'partial': '#ffc107',
        'minimum': '#dc3545',
        'no': '#6c757d'
    }
    return colors.get(threshold_type, '#6c757d')
