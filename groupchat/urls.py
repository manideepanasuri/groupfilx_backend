from django.urls import path
from .views import CreateGroupView, AddMemberView

urlpatterns = [
    path('create/', CreateGroupView.as_view(), name='create-group'),
    path('addmember/', AddMemberView.as_view(), name='add-member'),
]
