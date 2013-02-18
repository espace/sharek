from django.db import models
from django.contrib.auth.models import User

gender = models.CharField(max_length=10,default='na')
gender.contribute_to_class(User, 'gender')