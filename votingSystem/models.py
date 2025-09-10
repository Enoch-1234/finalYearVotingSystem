# votingSystem/models.py
from django.db import models
from django.utils import timezone
from account.models import Student

class Block(models.Model):
    index = models.IntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)
    vote_data = models.TextField()  # Encrypted or hashed vote
    previous_hash = models.CharField(max_length=256)
    hash = models.CharField(max_length=256)
    nonce = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.index}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    eligible_departments = models.ManyToManyField('account.Department')

    def __str__(self):
        return f"{self.name}"

    class Meta:
        permissions = [
            ("can_vote", "Can vote in categories"),
            ("can_view_results", "Can view voting results"),
            ("can_verify_blockchain", "Can verify blockchain integrity"),
        ]


class Candidate(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='candidates/')

    def __str__(self):
        return f"{self.name} - {self.category}"
