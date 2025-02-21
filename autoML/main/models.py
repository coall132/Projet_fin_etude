from django.conf import settings
from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()

import uuid
from django.conf import settings
from django.db import models

class Project(models.Model):
    """Table qui stocke les projets liés à un utilisateur"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="projets"
    )
    project_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False) 
    project_name = models.CharField(max_length=255)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'project_name')  # Empêche un même user d'avoir 2 projets du même nom

    def __str__(self):
        return self.projet_name


class Dataset(models.Model):
    """Table qui stocke les datasets liés à un projet"""
    project_id = models.ForeignKey(  # Utilisation de projet_id pour correspondre
        Project, 
        on_delete=models.CASCADE, 
        related_name="datasets"
    )
    dataset_name = models.CharField(max_length=255)  # Supprime l'unicité globale pour éviter les erreurs
    description = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('project_id', 'dataset_name')  

    def __str__(self):
        return f"{self.projet.project_name} - {self.dataset_name}"



class Graphique(models.Model):
    """Table des graphiques liés à un dataset"""
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE, 
        related_name="graphiques"
    )
    graphique = models.CharField(max_length=100, unique=True)  # Champ de nom du graphique
    donnees = models.JSONField()

    def __str__(self):
        return self.graphique
