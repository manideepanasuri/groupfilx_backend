from django.db import models
from django.conf import settings

from movies.models import Movie

User = settings.AUTH_USER_MODEL

class Group(models.Model):
    name = models.CharField(max_length=255)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_groups')
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='messages')
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} @ {self.group}: {self.content[:20]}"


class Poll(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="polls")
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class PollOption(models.Model):
    poll = models.ForeignKey(Poll, on_delete=models.CASCADE, related_name="options")
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="poll_options")
    votes = models.ManyToManyField(User, blank=True, related_name="voted_poll_options")

    def __str__(self):
        return self.movie.title