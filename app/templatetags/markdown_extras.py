from django import template
from django.utils.safestring import mark_safe
import markdown
import re
from bleach import clean

register = template.Library()

@register.filter(name='markdown_format')
def markdown_format(text):
    if not text:
        return ""
        
    # Replace ||spoiler text|| with spoiler span blocks
    text = re.sub(r'\|\|(.*?)\|\|', r'<span class="spoiler mitsulist-spoiler">\1</span>', text)
    
    # Allowed tags mapping
    allowed_tags = [
        'p', 'strong', 'em', 'del', 'a', 'h1', 'h2', 'h3', 'ul', 'ol', 'li', 
        'blockquote', 'pre', 'code', 'br', 'span', 'hr'
    ]
    allowed_attributes = {
        'a': ['href', 'title', 'target'], 
        'span': ['class'],
    }
    
    md = markdown.markdown(text, extensions=['fenced_code', 'nl2br', 'sane_lists'])
    cleaned = clean(md, tags=allowed_tags, attributes=allowed_attributes)
    
    return mark_safe(cleaned)
