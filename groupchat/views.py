from django.shortcuts import render

# Create your views here.
from rest_framework import generics, permissions, status
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Group, Message, Poll
from .serializers import GroupSerializer, MessageSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

class CreateGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user=request.user
        group=Group.objects.filter(members=user)
        serializer=GroupSerializer(group,many=True)
        return Response(serializer.data, status=HTTP_200_OK)

    def post(self, request):
        name = request.data.get("name")
        if not name:
            return Response({"error": "Group name is required"}, status=status.HTTP_400_BAD_REQUEST)

        # create group
        group = Group.objects.create(name=name, admin=request.user)
        group.members.add(request.user)

        serializer = GroupSerializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AddMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        group_id = request.data.get('group_id')
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=404)

        if group.admin != request.user:
            return Response({'error': 'Only admin can add members'}, status=403)

        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)

        group.members.add(user)
        return Response({'message': 'Member added'},status=HTTP_200_OK)

class PollsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        group_id = request.data.get('group_id')
        try:
            group = Group.objects.get(id=group_id)
            user=request.user
            if not group.members.filter(user=user).exists():
                return Response({'error': 'Group not found'}, status=404)
            polls = Poll.objects.filter(group=group)
        except Group.DoesNotExist:
            return Response({'error': 'Group not found'}, status=404)