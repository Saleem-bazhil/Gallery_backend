from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'photos', PhotoViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('photos/<int:photo_id>/toggle-favorite/', ToggleFavoriteView.as_view(), name='toggle-favorite'),

]
