import os
import django
from django.utils import timezone

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
django.setup()

from exams.models import Exam

now = timezone.now()
print(f"Now: {now}")
print("Published exams:")
for e in Exam.objects.filter(status='published'):
    print(f"- {e.title}: start={e.start_time}, end={e.end_time}, available={e.start_time <= now <= e.end_time}")
