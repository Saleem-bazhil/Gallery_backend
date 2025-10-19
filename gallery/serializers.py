from rest_framework import serializers
from .models import Photo

class PhotoSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Photo
        fields = ['id', 'name', 'img','image', 'category', 'date', 'is_favorite']
        read_only_fields = ['date','image']

    def get_image(self, obj):
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.img.url)
        return obj.img.url
