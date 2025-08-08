from django import template
import calendar
import locale

register = template.Library()

@register.filter(name='month_name')
def month_name(month_number):
    """
    Returns the name of the month for the given month number (1-12)
    """
    try:
        # Try to use locale-specific month names
        month_number = int(month_number)
        if 1 <= month_number <= 12:
            # Get month name in current locale
            return calendar.month_name[month_number]
        return ""
    except (ValueError, TypeError):
        return ""

@register.filter(name='div')
def div(value, divisor):
    """
    Divise une valeur par un diviseur
    """
    try:
        return float(value) / float(divisor)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter(name='mul')
def mul(value, multiplier):
    """
    Multiplie une valeur par un multiplicateur
    """
    try:
        return float(value) * float(multiplier)
    except (ValueError, TypeError):
        return 0

@register.filter(name='sub')
def sub(value, arg):
    """
    Soustrait arg de value
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
