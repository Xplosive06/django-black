from django.shortcuts import render
from django.http import JsonResponse
import requests
import pandas as pd

# Chemin du fichier CSV
file_path = "data/df_movies.csv"

df_films = pd.read_csv(file_path)

from sklearn.neighbors import NearestNeighbors

# Cleaning
colonnes = ['movie_title','title_year','genres','duration','budget','imdb_score','actor_1_name','director_name']
df_movies = df_films[colonnes].copy()
df_movies.dropna(inplace=True)
df_movies['movie_title'] = df_movies['movie_title'].str.strip()
df_movies.reset_index(drop=True, inplace=True)

# Features
features_text = ['genres', 'actor_1_name', 'director_name']
features_num = ['title_year', 'duration', 'budget', 'imdb_score']

# Traitement du genre
df_dummies = df_movies['genres'].str.get_dummies(sep="|")
df_movies2 = pd.concat([df_movies, df_dummies], axis=1)
df_movies2.drop("genres", axis=1, inplace=True)

# Traitement de 'actor_1_name' et 'director_name'
features_text2 = ['actor_1_name', 'director_name']
df_movies2 = pd.get_dummies(df_movies2, columns=features_text2, dtype="int", prefix=None)

# Subset d'apprentissage
X = df_movies2.drop("movie_title", axis=1)

def get_movie_recommendations(cible, boost_score=False, nameListOnly=True):
  '''
  Fonction de recommandation
    Paramètres :
      cible : str - nom du film de référence
      boost_score : Boolean (default = False) 
      nameListOnly : Boolean (default = True)
    -------
    Si boost_score = True
      - ramène 10 recommandations et retourne les 5 meilleurs imdb_score
    sinon
      - retourne les 5 meilleurs recommandations 
    -------
    Si nameListOnly = True
      - renvoie juste la liste des noms de films recommandés
    sinon
      - renvoie un dataframe des films recommandés 
  '''
  
  # Paramètres de la cible
  y = df_movies2.loc[df_movies2.movie_title==cible].drop("movie_title", axis=1)
  
  if boost_score:
    # Apprentissage
    distanceKNN2 = NearestNeighbors(n_neighbors=10).fit(X)
    # Les proches voisins
    voisins = distanceKNN2.kneighbors(y)
    df_voisins = df_movies.iloc[voisins[1][0][1:]].sort_values(by="imdb_score", ascending=False).head()
    if nameListOnly:
      return df_voisins.movie_title.to_list()
    else:
      return df_voisins
  else:
    # Apprentissage
    distanceKNN2 = NearestNeighbors(n_neighbors=6).fit(X)
    # Les proches voisins
    voisins = distanceKNN2.kneighbors(y)
    df_voisins = df_movies.iloc[voisins[1][0][1:]] #.head()
    if nameListOnly:
      return df_voisins.movie_title.to_list()
    else:
      return df_voisins

def get_movie_poster_url(movie_title):
    # Récupérer le lien IMDB du film
    imdb_link = df_films[df_films['movie_title'] == movie_title]['movie_imdb_link'].values[0]
    # Extraire l'ID du film à partir du lien IMDB
    tt_id = imdb_link.split('/')[4]

    # Appeler l'API pour récupérer les informations du film
    url = f"https://api.themoviedb.org/3/find/{tt_id}?external_source=imdb_id"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI1OGQ1MTg2ODc5Y2Y4NjJmZTYyMTQwYTljNmViNGFlMiIsInN1YiI6IjVmYWQwM2QzZDdmYmRhMDAzZDk3ZDc0NiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.waE5IPpm0NeuZ17E5FjkqJWIGLpmR11pITDjEOBvqOM"
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    # Accéder à "poster_path" dans le dictionnaire de résultats
    poster_path = data["movie_results"][0]["poster_path"]

    # Construire l'URL complète du poster
    poster_url = "https://image.tmdb.org/t/p/original" + poster_path
    return poster_url

def index(request):
    # Récupérer les titres de films disponibles dans df_movies['movie_title']
    movie_titles = df_movies['movie_title'].tolist()
    # Change all movie titles with single quotes to double quotes
    # movie_titles = json.dumps(movie_titles)
    return render(request, 'pages/dashboard.html', {'movie_titles': movie_titles})

def search_movies(request):
    if request.method == 'POST':
        # Récupérer les termes de recherche depuis la requête POST
        search_query = request.POST.get('search_query', '')
        recommendations = get_movie_recommendations(search_query, True, True)

        # Créer une liste pour stocker les informations des films recommandés
        search_results = []
        for movie_title in recommendations:
            # Récupérer les informations du film
            movie_info = df_films[df_films['movie_title'] == movie_title].iloc[0]
            title_year = str(int(movie_info['title_year']))
            duration = f"{int(movie_info['duration']) // 60}h{int(movie_info['duration']) % 60}m"
            genres = movie_info['genres']
            imdb_score = str(movie_info['imdb_score'])
            movie_imdb_link = movie_info['movie_imdb_link']
            poster_url = get_movie_poster_url(movie_title)  # Ajout du poster_url ici

            # Créer un dictionnaire pour stocker les informations du film
            movie_data = {
                'title': movie_title,
                'title_year': title_year,
                'duration': duration,
                'genres': genres,
                'imdb_score': imdb_score,
                'movie_imdb_link': movie_imdb_link,
                'poster_url': poster_url  # Ajout du poster_url dans le dictionnaire
            }

            # Ajouter le dictionnaire à la liste search_results
            search_results.append(movie_data)

        # Créer une liste pour stocker les URLs des posters des films recommandés
        poster_urls = [get_movie_poster_url(movie_title) for movie_title in recommendations]

        # Renvoyer les résultats au format JSON
        return JsonResponse({'results': search_results, 'poster_urls': poster_urls})

def tables(request):
    return render(request, 'pages/tables.html', {})

def histogram_data(request):
    # Récupérer les données de durée des films depuis le DataFrame df_movies
    duration_data = df_movies['duration'].tolist()

    # Renvoyer les données au format JSON
    return JsonResponse(duration_data, safe=False)

def movies_per_year_data(request):
    # Compter le nombre de films produits chaque année
    movies_per_year = df_movies['title_year'].value_counts().sort_index()
    movies_per_year_data = {
        'years': movies_per_year.index.tolist(),
        'count': movies_per_year.values.tolist()
    }

    # Renvoyer les données au format JSON
    return JsonResponse(movies_per_year_data)

def films_by_country_data(request):
    # Récupérer le nombre de films par pays
    films_by_country = df_movies['country'].value_counts()

    # Sélectionner les 5 premiers pays avec le plus grand nombre de films
    top_5_countries = films_by_country.head(5)

    # Calculer le nombre total de films pour les autres pays
    other_countries_total = films_by_country.iloc[5:].sum()

    # Créer un DataFrame avec les 5 premiers pays et la catégorie "Autres"
    top_countries_and_other = pd.DataFrame({'Pays': top_5_countries.index, 'Nombre de films': top_5_countries.values})
    top_countries_and_other.loc[len(top_countries_and_other)] = ['Autres', other_countries_total]

    # Convertir le DataFrame en format JSON et le renvoyer comme réponse
    return JsonResponse(top_countries_and_other.to_dict())