from django.test import TransactionTestCase, AsyncClient
from django.urls import reverse
from unittest.mock import patch, AsyncMock
from .models import News

class AppViewsTest(TransactionTestCase):
    def setUp(self):
        self.client = AsyncClient()
        # Create some dummy news
        News.objects.create(title="Test News", description="Test Description")

    @patch('app.views.fetch_jikan_data', new_callable=AsyncMock)
    @patch('app.services.fetch_anime_recommendations', new_callable=AsyncMock)
    async def test_index_view(self, mock_recommendations, mock_fetch_jikan):
        """
        Test the index view with mocked API calls.
        Using AsyncClient to avoid AsyncToSync errors in async tests.
        """
        # Setup mock return values
        mock_data = {'data': [{'mal_id': 1, 'title': 'Test Anime', 'images': {'jpg': {'large_image_url': 'url'}}}]}
        mock_fetch_jikan.return_value = mock_data
        mock_recommendations.return_value = mock_data

        # Use async get
        response = await self.client.get(reverse('home'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertContains(response, 'Test News')
        self.assertContains(response, 'Test Anime')

    @patch('app.views.fetch_jikan_data', new_callable=AsyncMock)
    async def test_anime_detail_view(self, mock_fetch_jikan):
        mock_data = {
            'data': {
                'mal_id': 1, 
                'title': 'Test Anime', 
                'images': {'jpg': {'large_image_url': 'url'}},
                'type': 'TV',
                'status': 'Finished Airing',
                'synopsis': 'Test Synopsis'
            }
        }
        mock_fetch_jikan.return_value = mock_data
        
        response = await self.client.get(reverse('anime-view', args=[1]))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'anime-view.html')
        self.assertContains(response, 'Test Anime')
