# votingSystem/views.py
from django.urls import path
from. import views

urlpatterns = [
    path('', views.index, name='index'),
    path('vote/', views.vote, name='vote'),
    path('results/', views.results, name='results'),
    path('vote-confirmation/', views.vote_confirmation, name='vote_confirmation'),
    path('verify-vote/', views.verify_vote, name='verify_vote'),
]