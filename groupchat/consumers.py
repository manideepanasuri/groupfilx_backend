import json
from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.auth import AuthMiddlewareStack
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.models import CustomUser
from .models import Group, Message, Movie, Poll, PollOption
from .serializers import PollSerializer

User = CustomUser


# ===================== JWT Middleware =====================
class JWTAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            query_string = scope.get("query_string", b"").decode()
            if query_string:
                params = dict(x.split("=") for x in query_string.split("&"))
                token = params.get("token")
                if token:
                    user = await self.get_user(token)
                    scope['user'] = user
        except Exception as e:
            print(f"JWT Authentication Error: {e}")
        return await super().__call__(scope, receive, send)

    @sync_to_async
    def get_user(self, token):
        try:
            validated_data = JWTAuthentication().get_validated_token(token)
            return JWTAuthentication().get_user(validated_data)
        except Exception as e:
            print(f"Token Validation Error: {e}")
            return None


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))


# ===================== MAIN CHAT CONSUMER =====================
class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.group_id = self.scope['url_route']['kwargs']['group_id']
        self.room_group_name = f'chat_{self.group_id}'
        user = self.scope.get('user')

        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        is_member = await self.is_member(user.id, self.group_id)
        if not is_member:
            await self.close(code=4003)
            return

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        messages = await self.get_group_messages(self.group_id)
        polls = await self.get_active_polls(self.group_id)

        await self.send(text_data=json.dumps({
            "type": "init",
            "messages": messages,
            "active_polls": polls
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = self.scope['user']

        match data.get('type'):
            case 'message':
                content = data.get('message', '').strip()
                if not content:
                    return
                msg = await self.create_message(user.id, int(self.group_id), content)
                await self.channel_layer.group_send(self.room_group_name, {
                    'type': 'chat_message',
                    'message': msg,
                })

            case 'poll_create':
                poll_title = data.get("poll_title", "")
                movie_ids = data.get("movie_ids", [])
                poll = await self.create_poll(self.group_id, user.id, poll_title, movie_ids)

                await self.channel_layer.group_send(self.room_group_name, {
                    "type": "poll_broadcast",
                    "poll": poll,
                })

            case 'poll_vote':
                poll_id = data.get("poll_id")
                movie_id = data.get("movie_id")
                await self.record_vote(poll_id, user.id, movie_id)
                updated_poll = await self.get_poll(poll_id)

                await self.channel_layer.group_send(self.room_group_name, {
                    "type": "poll_update",
                    "poll": updated_poll,
                })

            case 'poll_close':
                poll_id = data.get("poll_id")
                success = await self.close_poll(poll_id, user.id)

                if success:
                    await self.channel_layer.group_send(self.room_group_name, {
                        "type": "poll_closed",
                        "poll_id": poll_id,
                    })
                else:
                    await self.send(text_data=json.dumps({
                        "type": "error",
                        "message": "Only the poll creator or group admin can close this poll."
                    }))

    # ===================== EVENT HANDLERS =====================
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "type": "message",
            "message": event["message"]
        }))

    async def poll_broadcast(self, event):
        await self.send(text_data=json.dumps({
            "type": "poll_create",
            "poll": event["poll"]
        }))

    async def poll_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "poll_update",
            "poll": event["poll"]
        }))

    async def poll_closed(self, event):
        await self.send(text_data=json.dumps({
            "type": "poll_closed",
            "poll_id": event["poll_id"]
        }))

    # ===================== DATABASE HELPERS =====================
    @database_sync_to_async
    def is_member(self, user_id, group_id):
        try:
            g = Group.objects.get(id=group_id)
            return g.members.filter(id=user_id).exists()
        except Group.DoesNotExist:
            return False

    @database_sync_to_async
    def create_message(self, sender_id, group_id, content):
        sender = User.objects.get(id=sender_id)
        group = Group.objects.get(id=group_id)
        msg = Message.objects.create(sender=sender, group=group, content=content)
        return {
            "id": msg.id,
            "sender_id": msg.sender.id,
            "sender_name": msg.sender.name,
            "content": msg.content,
            "timestamp": msg.timestamp.isoformat()
        }

    @database_sync_to_async
    def get_group_messages(self, group_id):
        msgs = Message.objects.filter(group_id=group_id).order_by("timestamp")
        return [{
            "id": m.id,
            "sender_id": m.sender.id,
            "sender_name": m.sender.name,
            "content": m.content,
            "timestamp": m.timestamp.isoformat()
        } for m in msgs]

    @database_sync_to_async
    def create_poll(self, group_id, creator_id, title, movie_ids):
        user = User.objects.get(id=creator_id)
        group = Group.objects.get(id=group_id)
        poll = Poll.objects.create(group=group, created_by=user, title=title)
        for mid in movie_ids:
            movie = Movie.objects.get(id=mid)
            PollOption.objects.create(poll=poll, movie=movie)
        return PollSerializer(poll).data

    @database_sync_to_async
    def get_poll(self, poll_id):
        poll = Poll.objects.get(id=poll_id)
        return PollSerializer(poll).data

    @database_sync_to_async
    def get_active_polls(self, group_id):
        polls = Poll.objects.filter(group_id=group_id, is_active=True)
        return PollSerializer(polls, many=True).data

    @database_sync_to_async
    def record_vote(self, poll_id, user_id, movie_id):
        poll = Poll.objects.get(id=poll_id)
        user = User.objects.get(id=user_id)
        if not poll.is_active:
            return False

        options = PollOption.objects.filter(poll=poll)
        for opt in options:
            if user in opt.votes.all():
                opt.votes.remove(user)

        selected = options.get(movie_id=movie_id)
        selected.votes.add(user)
        return True

    @database_sync_to_async
    def close_poll(self, poll_id, user_id):
        poll = Poll.objects.get(id=poll_id)
        user = User.objects.get(id=user_id)
        if poll.created_by == user or poll.group.admin == user:
            poll.is_active = False
            poll.save()
            return True
        return False
