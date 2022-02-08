from django.db import models
from numpy import ma

# Create your models here.

#crear una classe por cada tabla que necesites
#Django crea una tabla sin necesidad SQL

class Users(models.Model):
    nombre=models.CharField(max_length=50)
    direccion=models.CharField(max_length=50)
    email=models.EmailField()
    telefono=models.CharField(max_length=7)
    age=models.IntegerField(max_length=3)

class Empresas(models.Model):
    nombre = models.CharField(max_length=50)


