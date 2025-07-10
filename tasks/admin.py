# tasks/admin.py

from django.contrib import admin
from .models import Task, Project

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'project', 'priority', 'status', 'due_date', 'created_by']
    list_filter = ['priority', 'status', 'project']
    search_fields = ['title', 'description']

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']