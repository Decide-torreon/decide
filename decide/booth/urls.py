from django.urls import path
from .views import BoothView


urlpatterns = [
    #path('<int:voting_id>/', BoothView.as_view()),
    path('<str:voting_url>/', BoothView.as_view()),
]
