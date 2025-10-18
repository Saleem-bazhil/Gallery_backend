from rest_framework import serializers
from .models import Photo

class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(source='img', use_url=True) 
      
    class Meta:
        model = Photo
        fields = ['id', 'name', 'image', 'category', 'date','is_favorite']  
        read_only_fields = ['date']  
