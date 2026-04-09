from django.core.cache import cache

def api_health(request):
    """
    Context processor to inject global API health status into all templates.
    """
    return {
        'jikan_api_unhealthy': cache.get('jikan_api_unhealthy', False)
    }
