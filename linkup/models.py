 # Below imports are required to create and recongise classes

from django.db import models
from django.contrib.auth.models import User
from PIL import Image

from linkup.constants import (
    event_category_choices,
    event_importance_choices,
    privacy_choices,
    state_choices
)
from linkup.constants import PrivacyChoices, StateChoices

from django.db import models
from django.contrib.auth.models import User
from PIL import Image

# Each class I define is a section of table in the database initialised in settings.py


# Profile model used for uploading of photos
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.png', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} Profile'
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        img = Image.open(self.image.path)
        if img.width >300 or img.height >300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.image.path)

# url This model saves DateTime Choices for original event organizor
class DatetimeChoice(models.Model):
    content = models.CharField(max_length=255)
    event = models.ForeignKey('Event', related_name='datetime_choices', null=True, on_delete=models.SET_NULL)
    def __unicode__(self):
        return self.content

 # Location choices
class LocationChoice(models.Model):
    content = models.CharField(max_length=255)
    event = models.ForeignKey('Event', related_name='location_choices', null=True, on_delete=models.SET_NULL)

    def __unicode__(self):
        return self.content


 # Creation of event table
class Event(models.Model):
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    category = models.IntegerField(choices=event_category_choices)
  # url = models.SlugField(max_length=50)
    importance = models.IntegerField(choices=event_importance_choices)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    privacy = models.IntegerField(choices=privacy_choices, default=PrivacyChoices.PUBLIC)
    invited_users = models.ManyToManyField(User, blank=True, related_name='invited_events')
    state = models.IntegerField(choices=state_choices, default=StateChoices.OPENED)
    creator = models.ForeignKey(User, null=True,blank=True,  on_delete=models.DO_NOTHING)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

 # Creation of polls table
class Poll(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    multi_choices = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    creator = models.ForeignKey(User, null=True,blank=True, on_delete=models.CASCADE)
    privacy = models.IntegerField(choices=privacy_choices, default=PrivacyChoices.PUBLIC)
    state = models.IntegerField(choices=state_choices, default=StateChoices.OPENED)
    invited_users = models.ManyToManyField(User, blank=True, related_name='invited_polls')
 # Meta data info to be added for poll list, same applies for event
    class Meta:
        ordering = ['-created_at']
 #Return title of poll
    def __str__(self):
        return self.title

# Creation of event table
class PollChoice(models.Model):
    content = models.CharField(max_length=255)
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

    def __str__(self):
        return self.content
    def __unicode__(self):
        return self.content

class UserPollChoice(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name='user_choices')
    choices = models.ManyToManyField(PollChoice)
    creator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    email = models.CharField(max_length=255, null=True)

    def __str__(self):
        if self.creator:
            return '{create_username}'.format(
                create_username=self.creator.username
            )
        else:
            return ''

    def get_full_name(self):
        if not self.creator:
            return
        return '{create_username}'.format(
            create_username=self.creator.username
        )



class UserEventChoice(models.Model):
    event = models.ForeignKey(Event, null=True, on_delete=models.SET_NULL)
    datetime_choices = models.ManyToManyField(DatetimeChoice)
    location_choices = models.ManyToManyField(LocationChoice)
    creator = models.ForeignKey(User, on_delete=models.DO_NOTHING)

    def __str__(self):
        return '{create_username}'.format(
            create_username=self.creator.username)
    def get_full_name(self):
        if not self.creator:
            return
        return '{create_username}'.format(
            create_username=self.creator.username
        )
