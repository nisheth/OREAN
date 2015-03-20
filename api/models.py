from django.db import models
from django.contrib.auth.models import User, UserManager
import string 
import random
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from rest_framework.authtoken.models import Token

class GetOrNoneManager(models.Manager):
    """Adds get_or_none method to objects
    """
    def get_or_none(self, **kwargs):
        try:
            return self.get(**kwargs)
        except self.model.DoesNotExist:
            return None

# Hook to create token for new users when they are created
@receiver(post_save, sender=get_user_model())
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)

#Method creates a random api key string when users are created
def generateapikey(size=16, chars=string.ascii_letters):
    return "".join(random.choice(chars) for _ in range(size))


# subject map
class SubjectMap(models.Model):
    project = models.ForeignKey('Project')
    subject = models.CharField(max_length=255)
    visit = models.CharField(max_length=255)
    sample = models.CharField(max_length=255)

# Project table
class Project(models.Model):
    name=models.CharField(max_length=255, unique=True)
    public=models.BooleanField(default=False)
    user=models.ForeignKey(User)
    invitecode = models.CharField(max_length=40, unique=True)

    def __unicode__(self):
       return "%s" % self.name

    def is_timecourse(self):
       return SubjectMap.objects.filter(project=self).exists()

# Maps which users can access which projects
# and who can manage each project
class UserProject(models.Model):
    user=models.ForeignKey(User)
    project = models.ForeignKey(Project)
    manager = models.BooleanField(default=False)

# Query Table stores query information
# SQL string = Raw SQL ran
# results = the sample ids that match that query    
class Query(models.Model):
    user=models.ForeignKey(User)
    project = models.ForeignKey(Project)
    name=models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    sqlstring = models.TextField(null=True, blank=True)
    results = models.TextField()
    share = models.IntegerField(default=0)

    @property
    def samplecount(self):
        return len(self.results.split(','))

    @property
    def expandsamples(self):
        return self.results.split(',')

    class Meta:
        unique_together = ("project", "name")

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

# Metadata for projects
class Attributes(models.Model):
    project = models.ForeignKey(Project)
    sample = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255)

# Analysis based data for projects
class Analysis(models.Model):
    project = models.ForeignKey(Project)
    sample = models.CharField(max_length=255, db_index=True)
    dataset = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=255, db_index=True)
    entity = models.CharField(max_length=255, db_index=True) 
    taxatree = models.ForeignKey('TaxaTree', null=True)
    numreads = models.IntegerField()
    profile = models.FloatField()
    avgscore = models.FloatField()

    def __unicode__(self):
       return "%s" % self.id
    class Meta:
        index_together = [
            ["project", "sample"],
            ["project", "dataset"],
            ["project", "dataset", "method"],
            ["project", "dataset", "method", "category"],
        ]

# Tracks access permissions for user registration and password reset
class EmailTokens(models.Model):
    TYPE_CHOICES = (
      (1, 'registration'),
      (2, 'resetpassword'),
    )
  
   
    user = models.ForeignKey(User)
    type = models.IntegerField(choices=TYPE_CHOICES)
    datetime = models.DateTimeField(auto_now_add=True)
    token = models.CharField(max_length=32, unique=True)

# Tracks which projects new users can be added to from invitations
class Invitations(models.Model):
    email = models.EmailField()
    project = models.ForeignKey(Project)
    user = models.ForeignKey(User)
    timedate = models.DateTimeField(auto_now_add=True)

# Tracks which project each user is currently working on
class ActiveProject(models.Model):
    user = models.ForeignKey(User, unique=True)
    project = models.ForeignKey(Project)
    objects = GetOrNoneManager()

# Stores calculations that are atomic to a single sample
class Calculation(models.Model):
    project = models.ForeignKey(Project)
    sample = models.CharField(max_length=255, db_index=True)
    dataset = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=255, db_index=True)
    calculation = models.CharField(max_length=255, db_index=True)
    value = models.FloatField()

# Stores calculations that compare two samples
class PairwiseCalculation(models.Model):
    project = models.ForeignKey(Project)
    sample1 = models.CharField(max_length=255, db_index=True)
    sample2 = models.CharField(max_length=255, db_index=True)
    dataset = models.CharField(max_length=255, db_index=True)
    method = models.CharField(max_length=255, db_index=True)
    category = models.CharField(max_length=255, db_index=True)
    calculation = models.CharField(max_length=255, db_index=True)
    value = models.FloatField()

# Stores information about reference taxonomy
class Taxonomy(models.Model):
    name = models.CharField(max_length=255, db_index=True, unique=True)
    description = models.TextField()
    url = models.URLField(max_length=255)
    datestamp = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return self.name


# Stores heirarchical information about reference
# taxonomy
# note that parent id is null for a root node
class TaxaTree(models.Model):
    taxonomy = models.ForeignKey(Taxonomy)
    tax_id = models.IntegerField()
    tax_name = models.CharField(max_length=255)    
    tax_level = models.CharField(max_length=255)    
    parent_id = models.ForeignKey('self', blank=True, null=True)
    full_tree = models.TextField()

    class Meta:
        unique_together = ('taxonomy', 'tax_id')
        index_together = [
            ["taxonomy", "tax_id"],
        ]

class UploadedFile(models.Model):

    FILE_TYPES = (
 	('analysis', 'analysis'),
        ('metadata', 'metadata'),
        ('taxonomy', 'taxonomy'),
    )

    type = models.CharField(max_length=255, choices = FILE_TYPES)
    datestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    project = models.ForeignKey(Project, null=True, blank=True)
    file = models.FileField(upload_to="uploads")
