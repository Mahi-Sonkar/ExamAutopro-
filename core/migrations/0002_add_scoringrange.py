# Generated manually to fix model conflicts

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScoringRange',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Name of this scoring rule', max_length=100)),
                ('description', models.TextField(blank=True, help_text='Description of when this rule applies', null=True)),
                ('min_score', models.FloatField(default=0.0, help_text='Minimum similarity score (0.0 to 1.0)')),
                ('max_score', models.FloatField(default=1.0, help_text='Maximum similarity score (0.0 to 1.0)')),
                ('marks', models.IntegerField(help_text='Marks to award for this similarity range')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(limit_choices_to={'role': 'teacher'}, on_delete=django.db.models.deletion.CASCADE, related_name='core_scoring_ranges', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Scoring Range',
                'verbose_name_plural': 'Scoring Ranges',
                'ordering': ['-min_score'],
            },
        ),
    ]
