from rest_framework import serializers
from .models import FaceData

class FaceDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceData
        fields = ['id', 'username', 'image', 'created_at']
