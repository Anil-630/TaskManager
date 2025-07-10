# tasks/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Task, Project
from .forms import RegisterForm, TaskForm, ProjectForm

# Home page
def home(request):
    return render(request, 'home.html')

# Register
def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('dashboard')
    else:
        form = RegisterForm()
    return render(request, 'register.html', {'form': form})

# Dashboard
@login_required
def dashboard(request):
    tasks = Task.objects.all()
    projects = Project.objects.all()
    return render(request, 'dashboard.html', {'tasks': tasks, 'projects': projects})

# Create Task
@login_required
def create_task(request):
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            messages.success(request, 'Task created!')
            return redirect('dashboard')
    else:
        form = TaskForm()
    return render(request, 'create_task.html', {'form': form})

# Edit Task
@login_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not request.user.is_superuser and task.created_by != request.user:
        messages.error(request, 'No permission!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task)
        if form.is_valid():
            form.save()
            messages.success(request, 'Task updated!')
            return redirect('dashboard')
    else:
        form = TaskForm(instance=task)
    
    return render(request, 'edit_task.html', {'form': form, 'task': task})

# Delete Task
@login_required
def delete_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    
    # Check permission
    if not request.user.is_superuser and task.created_by != request.user:
        messages.error(request, 'No permission!')
        return redirect('dashboard')
    
    task.delete()
    messages.success(request, 'Task deleted!')
    return redirect('dashboard')

# Create Project (Admin only)
@login_required
def create_project(request):
    if not request.user.is_superuser:
        messages.error(request, 'Admin only!')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Project created!')
            return redirect('dashboard')
    else:
        form = ProjectForm()
    return render(request, 'create_project.html', {'form': form})