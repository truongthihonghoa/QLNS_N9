from rest_framework import serializers
from .models import ChiNhanh

class ChiNhanhSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChiNhanh
        fields = '__all__'