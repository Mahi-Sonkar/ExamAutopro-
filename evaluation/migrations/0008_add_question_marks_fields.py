# Generated migration for adding question and marks fields to ScoringRange

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0007_alter_evaluationresult_options'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoringrange',
            name='total_questions',
            field=models.IntegerField(default=0, help_text='Total number of questions in this evaluation'),
        ),
        migrations.AddField(
            model_name='scoringrange',
            name='total_marks',
            field=models.FloatField(default=0.0, help_text='Total marks for all questions'),
        ),
        migrations.AddField(
            model_name='scoringrange',
            name='marks_per_question',
            field=models.FloatField(default=0.0, help_text='Marks allocated per question'),
        ),
    ]
