from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.VotingView.as_view(), name='voting'),
    path('<int:voting_id>/', views.VotingUpdate.as_view(), name='voting'),
    path('<int:voting_id>/users/', views.VotingsPerUser.as_view(), name='votingsPerUser')
]
