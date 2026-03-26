import os
import django
import asyncio

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mitsulist.settings')
django.setup()

from django.test import AsyncRequestFactory
from app.views import index
from django.contrib.auth.models import User

async def run_test():
    factory = AsyncRequestFactory()
    request = factory.get('/')
    # Simulate logged in user
    user = await User.objects.afirst()
    if not user:
        print("No user found")
        return
        
    request.user = user
    try:
        response = await index(request)
        print(f"Response status: {response.status_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(run_test())
