"""
Fix Django migrations by creating migration files manually
Resolve model conflicts without running makemigrations
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ExamAutoPro.settings')
django.setup()

def create_migration_files():
    """Create migration files manually to fix model conflicts"""
    
    print("=== FIXING DJANGO MIGRATIONS ===")
    print()
    
    # Create migration for core app (ScoringRange model)
    core_migration = '''# Generated manually to fix model conflicts

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


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
'''
    
    # Create migration for evaluation app (fixing EvaluationLog)
    evaluation_migration = '''# Generated manually to fix model conflicts

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0001_initial'),
        ('exams', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='evaluationlog',
            options={'ordering': ['-timestamp']},
        ),
        migrations.AlterModelFields(
            name='evaluationlog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(default='evaluated', max_length=100)),
                ('details', models.TextField(default='')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('answer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exams.answer')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
'''
    
    # Write migration files
    migrations_dir = 'evaluation\\migrations'
    
    # Ensure migrations directory exists
    if not os.path.exists(migrations_dir):
        os.makedirs(migrations_dir)
    
    # Write evaluation migration
    evaluation_file = os.path.join(migrations_dir, '0002_fix_evaluationlog.py')
    with open(evaluation_file, 'w') as f:
        f.write(evaluation_migration)
    
    print(f"Created migration: {evaluation_file}")
    
    # Create core migrations directory if needed
    core_migrations_dir = 'core\\migrations'
    if not os.path.exists(core_migrations_dir):
        os.makedirs(core_migrations_dir)
    
    # Write core migration
    core_file = os.path.join(core_migrations_dir, '0002_add_scoringrange.py')
    with open(core_file, 'w') as f:
        f.write(core_migration)
    
    print(f"Created migration: {core_file}")
    
    print()
    print("Migration files created manually!")
    print("Now run: python manage.py migrate")

if __name__ == "__main__":
    create_migration_files()
