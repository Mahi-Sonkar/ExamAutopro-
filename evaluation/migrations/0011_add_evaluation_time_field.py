# Generated manually to fix missing evaluation_time column

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0010_add_evaluation_models'),
    ]

    operations = [
        migrations.AddField(
            model_name='evaluationresult',
            name='evaluation_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
