from django import template

register = template.Library()


@register.filter()
def multiply(value, arg):
    return value * arg


@register.filter()
def trim_zeros(value):
    nums = str(value).split('.')
    stripped = nums[1].rstrip('0')
    while len(stripped) < 4:
        stripped += '0'
    return '{}.{}'.format(nums[0], stripped)
