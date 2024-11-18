from django.http import JsonResponse
# from rest_framework.decorators import api_view 
from adrf.decorators import api_view 
from rest_framework.response import Response 
from rest_framework import status 
import requests
from .models import Query, Movie
from .serializers import QuerySerializer 
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import urllib.parse
import asyncio
from django.db import connection
from asgiref.sync import sync_to_async

#comment

def store_db_helper(id):
    encoded_url = "https://caching.graphql.imdb.com/?operationName=TMD_Storyline&variables=%7B%22isAutoTranslationEnabled%22%3Afalse%2C%22locale%22%3A%22en-US%22%2C%22titleId%22%3A%22tt0816692%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%228693f4655e3e7c5b6f786c6cf30e72dfa63a8fd52ebbad6f3a5ef7f03431c0f1%22%2C%22version%22%3A1%7D%7D"

    
    parsed_url = urllib.parse.urlparse(encoded_url)
    query_params = urllib.parse.parse_qs(parsed_url.query)

    
    variables = json.loads(query_params['variables'][0])
    extensions = json.loads(query_params['extensions'][0])

    
    new_title_id = id  
    variables['titleId'] = new_title_id

    
    modified_query_params = {
        'operationName': query_params['operationName'][0],
        'variables': json.dumps(variables),
        'extensions': json.dumps(extensions)
    }

    # Correctly encode the JSON strings without double encoding
    encoded_query_string = urllib.parse.urlencode(modified_query_params, quote_via=urllib.parse.quote)
    modified_encoded_url = f"https://{parsed_url.netloc}{parsed_url.path}?{encoded_query_string}"
    print("Modified Encoded URL:", modified_encoded_url)

    
    headers = {
        "Accept": "application/graphql+json, application/json",
        "Content-Type": "application/json",
        "Referer": "https://www.imdb.com/",
        "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "X-Amzn-Sessionid": "133-4283144-0739261",
        "X-Imdb-Client-Name": "imdb-web-next-localized",
        "X-Imdb-Client-Rid": "MHGPCTYPYEWESXFYQBCJ",
        "X-Imdb-User-Country": "US",
        "X-Imdb-User-Language": "en-US",
        "X-Imdb-Weblab-Treatment-": '{"IMDB_NAV_PRO_FLY_OUT_Q1_REFRESH_848923":"T1"}'
    }

    response = requests.get(modified_encoded_url, headers=headers)

    # Print response status code and content
    # print("Status Code:", response.status_code)
    # print("Response Content:", response.content)
    #print(response.json())
    # Try to parse the response as JSON if possible
    summary = ""
    synopse = ""
    try:
        data = response.json()
        #print("Response JSON:", data)
        for node in data['data']['title']['summaries']['edges']:
            summary = node['node']['plotText']['plaidHtml']
        for node in data['data']['title']['synopses']['edges']:
            synopse = node['node']['plotText']['plaidHtml']
    except requests.exceptions.JSONDecodeError:
        print("Failed to decode JSON response")
    
    return summary, synopse

def return_data(title):
    existing_query = Query.objects.filter(queryTitle=title).first()
    if existing_query:
        # Get all associated movies for the query
        #movie_set is the default reverse relationship created by Django because Movie has a ForeignKey relationship with Query. Since the Movie model is related to the Query model through a ForeignKey, Django creates a reverse relationship on the Query model named movie_set.
        #.all() retrieves all related Movie objects associated with the existing_query.
        movies = existing_query.movie_set.all()

        # Concatenate movie information
        movie_info = []
        for movie in movies:
            movie_info.append(f"Id: {movie.movie_id} Actors: {movie.movie_actors} Name: {movie.movie_name} Type: {movie.movie_type}")

        print(movie_info)
        return movie_info

    return "No data found"



def store_in_database(title, data):
    # Create a Query object
    query = Query(queryTitle=title)
    query.save()

    for obj in data['d']:
        # Create a Movie object associated with the Query object
        movie_id=str(obj['id'])
        summary, synopse = store_db_helper(movie_id)
        movie = Movie(
            query=query,  # Set the foreign key to the Query object
            movie_id=movie_id,
            movie_name=str(obj['l']),
            movie_type=str(obj['q']),
            movie_actors=str(obj['s']),
            movie_summary = summary,
            movie_synopses = synopse,
        )
        movie.save()
    

# @csrf_exempt
# @api_view(['GET','POST'])
# def get_movie(request):
#     if request.method == 'POST':
#         # Make an HTTP GET request to the desired URL
#         # title = request.query_params.get('title', None)
#         title = request.data

#         if not title:
#             return Response({'error': 'Movie ID not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
#         url = f'https://v3.sg.media-imdb.com/suggestion/x/{title}.json'  # Replace with the actual URL
#         try:
#             response = requests.get(url)
#             response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code

#             # Assuming the response is JSON, you can return it directly
#             data = response.json()
#             resp = modify_data(data)
#             return Response(resp, status=status.HTTP_200_OK)
        
#         except requests.exceptions.RequestException as e:
#             # Handle any errors that occur
#             return Response(data, status=status.HTTP_400_BAD_REQUEST)
        


@api_view(['GET','POST'])
@csrf_exempt
def get_movie(request):
    if request.method == 'POST':
        title = request.data

        if not title:
            return Response({'error': 'Movie title not provided'}, status=status.HTTP_400_BAD_REQUEST)

        existing_query = Query.objects.filter(queryTitle=title).first()
        if existing_query:
            return Response(return_data(title), status=status.HTTP_200_OK)
        
        url = f'https://v3.sg.media-imdb.com/suggestion/x/{title}.json'  
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an HTTPError if the HTTP request returned an unsuccessful status code

            data = response.json()
            
            

            store_in_database(title, data)

            resp = return_data(title)
   
            
            return Response(resp, status=status.HTTP_200_OK)
        
        except requests.exceptions.RequestException as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# @api_view(['GET'])
# @csrf_exempt
# def get_all_movie_titles(request):
#     if request.method == 'GET':
#         # Query all Movie objects and retrieve their titles
#         movie_titles = Query.objects.values_list('queryTitle', flat=True)
#         # Convert QuerySet to list for JSON serialization
#         movie_titles_list = list(movie_titles)
#         # Return the list of movie titles as a JSON response
#         return Response(movie_titles_list, status=status.HTTP_200_OK)
    


@api_view(['GET'])
@csrf_exempt
async def get_all_movie_titles(request):
    queryset = await sync_to_async(Query.objects.values_list)('queryTitle', flat=True)
   
    movie_titles = await sync_to_async(list)(queryset)
    return Response(movie_titles, status=status.HTTP_200_OK)

'''
import requests

url = "https://caching.graphql.imdb.com/?operationName=TMD_Storyline&variables=%7B%22isAutoTranslationEnabled%22%3Afalse%2C%22locale%22%3A%22en-US%22%2C%22titleId%22%3A%22tt0816692%22%7D&extensions=%7B%22persistedQuery%22%3A%7B%22sha256Hash%22%3A%228693f4655e3e7c5b6f786c6cf30e72dfa63a8fd52ebbad6f3a5ef7f03431c0f1%22%2C%22version%22%3A1%7D%7D"

headers = {
    "Accept": "application/graphql+json, application/json",
    "Content-Type": "application/json",
    "Referer": "https://www.imdb.com/",
    "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"macOS"',
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "X-Amzn-Sessionid": "133-4283144-0739261",
    "X-Imdb-Client-Name": "imdb-web-next-localized",
    "X-Imdb-Client-Rid": "MHGPCTYPYEWESXFYQBCJ",
    "X-Imdb-User-Country": "US",
    "X-Imdb-User-Language": "en-US",
    "X-Imdb-Weblab-Treatment-": '{"IMDB_NAV_PRO_FLY_OUT_Q1_REFRESH_848923":"T1"}'
}

response = requests.get(url, headers=headers)
data = response.json()

print(data)

'''
