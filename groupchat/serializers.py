from rest_framework import serializers

from users.models import CustomUser
from .models import Group, Message, Poll

User = CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email','name']

class GroupSerializer(serializers.ModelSerializer):
    admin = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'admin', 'members', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'sender', 'group', 'content', 'timestamp']

from rest_framework import serializers
from .models import Poll, PollOption
from movies.models import Movie
from users.models import CustomUser as User


class MovieSerializer2(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = ["id", "title", "poster_path","backdrop_path"]  # adjust fields as per your Movie model


class PollOptionSerializer(serializers.ModelSerializer):
    movie = MovieSerializer2(read_only=True)
    votes_count = serializers.SerializerMethodField()

    class Meta:
        model = PollOption
        fields = ["id", "movie", "votes_count"]

    def get_votes_count(self, obj):
        return obj.votes.count()


class PollSerializer(serializers.ModelSerializer):
    options = PollOptionSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source="created_by.name", read_only=True)
    total_votes = serializers.SerializerMethodField()

    class Meta:
        model = Poll
        fields = [
            "id",
            "title",
            "created_by",
            "created_by_name",
            "created_at",
            "is_active",
            "options",
            "total_votes",
        ]
        read_only_fields = ["created_by", "created_at", "is_active"]

    def get_total_votes(self, obj):
        """Count all votes in all options of the poll"""
        return sum(option.votes.count() for option in obj.options.all())

