from django import template

register = template.Library()


@register.inclusion_tag('navbar/navbar.html', takes_context=True)
def navbar(context,id):
    context = {
        'id': id,
        'request': context['request'],
    }
    return context
