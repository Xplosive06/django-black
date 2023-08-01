from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.search_movies, name='search_movies'),
    path('tables/', views.tables, name='tables'),
    path('histogram_data/', views.histogram_data, name='histogram_data'),
    path('movies_per_year_data/', views.movies_per_year_data, name='movies_per_year_data'),
    path('films_by_country_data/', views.films_by_country_data, name='films_by_country_data'),
]
