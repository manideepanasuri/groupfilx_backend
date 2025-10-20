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


class LeaveGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Allow a member to leave the group.
        If admin leaves, delete the group."""
        group_id = request.data.get('group_id')
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # --- If admin leaves, delete group ---
        if user == group.admin:
            group_name = group.name
            group.delete()
            return Response(
                {"message": f"The group '{group_name}' has been deleted since the admin left."},
                status=status.HTTP_200_OK
            )

        # --- Normal member leaves ---
        if user in group.members.all():
            group.members.remove(user)
            return Response({"message": "You have left the group."}, status=status.HTTP_200_OK)
        else:
            return Response({"error": "You are not a member of this group."}, status=status.HTTP_400_BAD_REQUEST)


class RemoveUserFromGroupView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        """Allow admin to remove a user from the group."""
        group_id = request.data.get('group_id')
        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response({"error": "Group not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user != group.admin:
            return Response({"error": "Only admin can remove members."}, status=status.HTTP_403_FORBIDDEN)

        user_id = request.data.get("user_id")
        if not user_id:
            return Response({"error": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_to_remove = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        if user_to_remove == group.admin:
            return Response({"error": "Admin cannot remove themselves."}, status=status.HTTP_400_BAD_REQUEST)

        if user_to_remove not in group.members.all():
            return Response({"error": "User is not a member of this group."}, status=status.HTTP_400_BAD_REQUEST)

        group.members.remove(user_to_remove)
        return Response(
            {"message": f"{user_to_remove.name} has been removed from the group."},
            status=status.HTTP_200_OK
        )