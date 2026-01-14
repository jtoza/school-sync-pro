from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.shortcuts import render

from .models import Homework
from .forms import HomeworkForm
from apps.corecode.models import StudentClass

class HomeworkListView(LoginRequiredMixin, ListView):
    model = Homework
    template_name = "homework/homework_list.html"
    context_object_name = "homework_list"

    def get_queryset(self):
        # Teachers see homework they posted
        return Homework.objects.filter(teacher=self.request.user)

class HomeworkCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Homework
    form_class = HomeworkForm
    template_name = "homework/homework_form.html"
    success_url = reverse_lazy("homework_list")
    success_message = "Homework posted successfully"

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)

class HomeworkUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Homework
    form_class = HomeworkForm
    template_name = "homework/homework_form.html"
    success_url = reverse_lazy("homework_list")
    success_message = "Homework updated successfully"

    def get_queryset(self):
        return Homework.objects.filter(teacher=self.request.user)

class HomeworkDeleteView(LoginRequiredMixin, DeleteView):
    model = Homework
    success_url = reverse_lazy("homework_list")
    template_name = "corecode/core_confirm_delete.html"
    
    def get_queryset(self):
        return Homework.objects.filter(teacher=self.request.user)

def student_homework_view(request):
    """Public view for students to check homework"""
    classes = StudentClass.objects.all()
    selected_class_id = request.GET.get('class_id')
    homework_list = []
    selected_class = None

    if selected_class_id:
        homework_list = Homework.objects.filter(student_class_id=selected_class_id).order_by('-created_at')
        try:
            selected_class = StudentClass.objects.get(id=selected_class_id)
        except StudentClass.DoesNotExist:
            pass

    context = {
        'classes': classes,
        'homework_list': homework_list,
        'selected_class': selected_class,
        'selected_class_id': int(selected_class_id) if selected_class_id else None
    }
    return render(request, 'homework/student_homework.html', context)
