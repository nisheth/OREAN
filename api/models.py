from django.db import models
from django.contrib.auth.models import User, UserManager
import string 
import random
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

#Method creates a random api key string when users are created
def generateapikey(size=16, chars=string.ascii_letters):
    return "".join(random.choice(chars) for _ in range(size))

# Custom User Model
# Extends user model to include api key
#class CustomUser(User):
#    apikey = models.CharField(max_length=16, unique=True, default=generateapikey())
#    objects = UserManager()

# Project table
class Project(models.Model):
    name=models.CharField(max_length=255, unique=True)

# Maps which users can access which projects
class UserProject(models.Model):
    user=models.ForeignKey(User)
    project = models.ForeignKey(Project)

# Query Table stores query information
# SQL string = Raw SQL ran
# results = the sample ids that match that query    
class Query(models.Model):
    user=models.ForeignKey(User)
    project = models.ForeignKey(Project)
    name=models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    sqlstring = models.TextField()
    results = models.TextField()
    share = models.IntegerField(default=0)

    @property
    def samplecount(self):
        return len(self.results.split(','))

    @property
    def expandsamples(self):
        return self.results.split(',')

# name = the name of the field in attributes table
# fieldtype = WHICH type to cast the data to during queries
# values = the possible values (string) or range(DECIMAL, DATE) for that field
class AttributeInfo(models.Model):
    CHOICES = (
        ('STRING', 'STRING'),
        ('DECIMAL', 'DECIMAL'),
        ('DATE', 'DATE'),
    )
    project = models.ForeignKey(Project)
    name=models.CharField(max_length=255)
    fieldtype = models.CharField(max_length=255, choices = CHOICES)
    values = models.TextField()

    @property
    def expandvalues(self):
        return self.values.split(',')

    class Meta:
        unique_together = (("project", "name"),)

class Attributes(models.Model):
    project = models.ForeignKey(Project)
    sample = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

class Analysis(models.Model):
    project = models.ForeignKey(Project)
    sample = models.CharField(max_length=255, db_index=True)
    dataset = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=255, db_index=True)
    entity = models.CharField(max_length=255, db_index=True) 
    numreads = models.IntegerField()
    profile = models.FloatField()
    avgscore = models.FloatField()
