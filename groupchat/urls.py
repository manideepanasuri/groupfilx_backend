from django.urls import path
from .views import CreateGroupView, AddMemberView, LeaveGroupView, RemoveUserFromGroupView

urlpatterns = [
    path('create/', CreateGroupView.as_view(), name='create-group'),
    path('addmember/', AddMemberView.as_view(), name='add-member'),
    path('leave/', LeaveGroupView.as_view(), name='add-member'),
    path('remove/', RemoveUserFromGroupView.as_view(), name='add-member'),
]
