from django.db import models

# Create your models here.
class Photo(models.Model):
    
    CATEGORY_CHOICES = [
        ('Camera', 'Camera'),
        ('Screenshot', 'Screenshot'),
        ('Album', 'Album'),
    ]
    
    name = models.CharField(max_length=255)  
    img = models.ImageField(upload_to='photos/') 
    date = models.DateTimeField(auto_now_add=True)  
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Camera')
    is_favorite = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.category})"