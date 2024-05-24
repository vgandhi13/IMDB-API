from django.db import models

class Query(models.Model):
    queryTitle = models.CharField(max_length=200)


    def __str__(self):
        return str(self.id) + ": " + self.queryTitle
    

class Movie(models.Model):
    query = models.ForeignKey(Query, on_delete=models.CASCADE) #this is the id of relevant Query obj,on_delete=models.CASCADE specifies the behavior when the referenced Query object is deleted. In this case, it will also delete all associated Movie objects.
    movie_id = models.CharField(max_length=100, primary_key=True)
    movie_name = models.CharField(max_length=255)
    movie_type = models.CharField(max_length=100)
    movie_actors = models.CharField(max_length=1000)
    movie_summary = models.CharField(max_length=65000)
    movie_synopses = models.CharField(max_length=65000)

    def __str__(self):
        return "Movie name: " + self.movie_name + " Movie Id: " + self.movie_id + " Type: " + self.movie_type + " Actors: " + self.movie_actors