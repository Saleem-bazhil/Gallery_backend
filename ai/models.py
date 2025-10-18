from django.db import models

class FaceData(models.Model):
    username = models.CharField(max_length=100)
    image = models.ImageField(upload_to='faces/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} - {self.id}"
