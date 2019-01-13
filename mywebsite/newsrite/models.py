from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

# Create your models here.


class Website(models.Model):
    website_name = models.CharField(max_length=100)
    website_url = models.CharField(default="",max_length=300)
    website_rating = models.IntegerField(default=0, validators=[MaxValueValidator(5), MinValueValidator(0)])

    def __str__(self):
        return self.website_name + ' - ' + str(self.website_rating)


class URL(models.Model):
    website = models.ForeignKey(Website, on_delete=models.CASCADE)
    query = models.CharField(max_length=300)
