# Generated migration for adding paper_image field to ScoringRange

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0008_add_question_marks_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='scoringrange',
            name='paper_image',
            field=models.ImageField(
                upload_to='scoring_ranges/papers/', 
                null=True, 
                blank=True, 
                help_text="Upload an image of the paper to automatically create a PDF analysis"
            ),
        ),
    ]
