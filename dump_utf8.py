import os
import django
import json
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core import serializers
from django.apps import apps

all_objects = []
for model in apps.get_models():
    all_objects.extend(model.objects.all())

with open('data.json', 'w', encoding='utf-8') as f:
    json.dump(
        json.loads(serializers.serialize("json", all_objects)),
        f,
        ensure_ascii=False,
        indent=2
    )

print("Dump thành công!")