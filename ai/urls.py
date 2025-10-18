from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *

# Router for FaceDataViewSet
router = DefaultRouter()
router.register(r'faces', FaceDataViewSet, basename='faces')

urlpatterns = [
    path('detect_face/', DetectFaceView.as_view(), name='detect-face'),  
    path("recognize_face/", RecognizeFaceView.as_view(), name="recognize-face"),
    path('', include(router.urls)),  
]
