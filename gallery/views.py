from django.shortcuts import render
from rest_framework.permissions import AllowAny
from rest_framework import viewsets
from .models import *
from .serializers import PhotoSerializer
from rest_framework.response import Response
from rest_framework.views import APIView


class PhotoViewSet(viewsets.ModelViewSet):
    queryset = Photo.objects.all().order_by('-date')  # newest first
    serializer_class = PhotoSerializer
    permission_classes = [AllowAny]
    
class ToggleFavoriteView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, photo_id):
        try:
            photo = Photo.objects.get(id=photo_id)
        except Photo.DoesNotExist:
            return Response({'error': 'Photo not found'}, status=404)

        # Toggle favorite
        photo.is_favorite = not photo.is_favorite
        photo.save()
        return Response({'id': photo.id, 'is_favorite': photo.is_favorite})