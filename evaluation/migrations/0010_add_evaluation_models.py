# Generated migration for adding QuestionPaper, Question, and EvaluationResult models

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('evaluation', '0009_add_paper_image_field'),
        ('pdf_analysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuestionPaper',
            fields=[
                ('id', models.UUIDField(primary_key=True, editable=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('created_by', models.ForeignKey('accounts.User', on_delete=django.db.models.deletion.CASCADE)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Question',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('question_paper', models.ForeignKey('evaluation.QuestionPaper', on_delete=django.db.models.deletion.CASCADE, related_name='questions')),
                ('question_number', models.PositiveIntegerField()),
                ('question_text', models.TextField()),
                ('question_type', models.CharField(max_length=20, default='short_answer')),
                ('marks', models.PositiveIntegerField()),
                ('model_answer', models.TextField(blank=True)),
            ],
            options={
                'ordering': ['question_number'],
                'unique_together': {('question_paper', 'question_number')},
            },
        ),
    ]
