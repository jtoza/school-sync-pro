from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse

from .models import LessonPlan, Subject, ClassLevel, LessonPlanAttachment, LessonPlanComment
from .forms import LessonPlanForm, LessonPlanFilterForm, LessonPlanAttachmentForm, LessonPlanCommentForm


class LessonPlanListView(LoginRequiredMixin, ListView):
    """View for listing lesson plans with filtering"""
    model = LessonPlan
    template_name = 'lessonplans/lessonplan_list.html'
    context_object_name = 'lessonplans'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = LessonPlan.objects.all()
        
        # For non-staff users, show only their own or visible lesson plans
        if not self.request.user.is_staff:
            queryset = queryset.filter(
                Q(teacher=self.request.user) |
                Q(visibility__in=['teachers', 'admin', 'students', 'parents', 'public'])
            )
        
        # Apply filters
        form = LessonPlanFilterForm(self.request.GET)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            class_level = form.cleaned_data.get('class_level')
            status = form.cleaned_data.get('status')
            visibility = form.cleaned_data.get('visibility')
            search = form.cleaned_data.get('search')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            
            if subject:
                queryset = queryset.filter(subject=subject)
            if class_level:
                queryset = queryset.filter(class_level=class_level)
            if status:
                queryset = queryset.filter(status=status)
            if visibility:
                queryset = queryset.filter(visibility=visibility)
            if search:
                queryset = queryset.filter(
                    Q(title__icontains=search) |
                    Q(objectives__icontains=search) |
                    Q(content__icontains=search) |
                    Q(tags__icontains=search)
                )
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
        
        return queryset.select_related('teacher', 'subject', 'class_level')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = LessonPlanFilterForm(self.request.GET)
        context['subjects'] = Subject.objects.all()
        context['class_levels'] = ClassLevel.objects.all()
        return context


class LessonPlanDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a single lesson plan"""
    model = LessonPlan
    template_name = 'lessonplans/lessonplan_detail.html'
    context_object_name = 'lessonplan'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Check permissions
        if not self.can_view(obj):
            raise PermissionDenied("You don't have permission to view this lesson plan.")
        
        return obj
    
    def can_view(self, lesson_plan):
        user = self.request.user
        
        # Teachers can always view their own lesson plans
        if lesson_plan.teacher == user:
            return True
        
        # Staff can view all lesson plans
        if user.is_staff:
            return True
        
        # Check visibility settings
        if lesson_plan.visibility == 'private':
            return False
        elif lesson_plan.visibility == 'admin' and not user.is_staff:
            return False
        elif lesson_plan.visibility == 'teachers' and not user.is_authenticated:
            return False
        elif lesson_plan.visibility in ['students', 'parents'] and not user.is_authenticated:
            return False
        
        return True
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['attachment_form'] = LessonPlanAttachmentForm()
        context['comment_form'] = LessonPlanCommentForm()
        context['can_edit'] = self.can_edit(self.object)
        return context
    
    def can_edit(self, lesson_plan):
        user = self.request.user
        return user == lesson_plan.teacher or user.is_staff


class LessonPlanCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new lesson plan"""
    model = LessonPlan
    form_class = LessonPlanForm
    template_name = 'lessonplans/lessonplan_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.teacher = self.request.user
        messages.success(self.request, 'Lesson plan created successfully!')
        return super().form_valid(form)


class LessonPlanUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an existing lesson plan"""
    model = LessonPlan
    form_class = LessonPlanForm
    template_name = 'lessonplans/lessonplan_form.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.teacher != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to edit this lesson plan.")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Lesson plan updated successfully!')
        return super().form_valid(form)


class LessonPlanDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting a lesson plan"""
    model = LessonPlan
    template_name = 'lessonplans/lessonplan_confirm_delete.html'
    success_url = reverse_lazy('lessonplans:list')
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.teacher != request.user and not request.user.is_staff:
            raise PermissionDenied("You don't have permission to delete this lesson plan.")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Lesson plan deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def add_attachment(request, pk):
    """View for adding an attachment to a lesson plan"""
    lesson_plan = get_object_or_404(LessonPlan, pk=pk)
    
    if lesson_plan.teacher != request.user and not request.user.is_staff:
        raise PermissionDenied("You don't have permission to add attachments to this lesson plan.")
    
    if request.method == 'POST':
        form = LessonPlanAttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.lesson_plan = lesson_plan
            attachment.save()
            messages.success(request, 'Attachment added successfully!')
    
    return redirect('lessonplans:detail', pk=pk)


@login_required
def delete_attachment(request, pk):
    """View for deleting an attachment"""
    attachment = get_object_or_404(LessonPlanAttachment, pk=pk)
    
    if attachment.lesson_plan.teacher != request.user and not request.user.is_staff:
        raise PermissionDenied("You don't have permission to delete this attachment.")
    
    lesson_plan_pk = attachment.lesson_plan.pk
    attachment.delete()
    messages.success(request, 'Attachment deleted successfully!')
    
    return redirect('lessonplans:detail', pk=lesson_plan_pk)


@login_required
def add_comment(request, pk):
    """View for adding a comment to a lesson plan"""
    lesson_plan = get_object_or_404(LessonPlan, pk=pk)
    
    # Check if user can view the lesson plan
    view_view = LessonPlanDetailView()
    view_view.request = request
    if not view_view.can_view(lesson_plan):
        raise PermissionDenied("You don't have permission to comment on this lesson plan.")
    
    if request.method == 'POST':
        form = LessonPlanCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.lesson_plan = lesson_plan
            comment.author = request.user
            comment.save()
            messages.success(request, 'Comment added successfully!')
    
    return redirect('lessonplans:detail', pk=pk)


@login_required
def toggle_comment_resolved(request, pk):
    """Toggle comment resolved status"""
    comment = get_object_or_404(LessonPlanComment, pk=pk)
    
    # Only the comment author, lesson plan teacher, or staff can resolve
    if not (comment.author == request.user or 
            comment.lesson_plan.teacher == request.user or 
            request.user.is_staff):
        raise PermissionDenied("You don't have permission to modify this comment.")
    
    comment.is_resolved = not comment.is_resolved
    comment.save()
    
    return JsonResponse({'resolved': comment.is_resolved})


class MyLessonPlansView(LoginRequiredMixin, ListView):
    """View for showing only the current user's lesson plans"""
    model = LessonPlan
    template_name = 'lessonplans/mylessonplans.html'
    context_object_name = 'lessonplans'
    paginate_by = 10
    
    def get_queryset(self):
        return LessonPlan.objects.filter(teacher=self.request.user).select_related('subject', 'class_level')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['stats'] = {
            'total': LessonPlan.objects.filter(teacher=self.request.user).count(),
            'draft': LessonPlan.objects.filter(teacher=self.request.user, status='draft').count(),
            'published': LessonPlan.objects.filter(teacher=self.request.user, status='published').count(),
            'review': LessonPlan.objects.filter(teacher=self.request.user, status='review').count(),
        }
        return context


def teacher_profile_view(request, username):
    """View for displaying a teacher's public profile with their lesson plans"""
    from django.contrib.auth.models import User
    teacher = get_object_or_404(User, username=username)
    
    # Get only published lesson plans that are visible to the requester
    lessonplans = LessonPlan.objects.filter(teacher=teacher, status='published')
    
    # Filter based on user's permissions
    if not request.user.is_authenticated:
        lessonplans = lessonplans.filter(visibility='public')
    elif request.user.is_staff:
        pass  # Staff can see all
    elif request.user == teacher:
        pass  # Teachers can see their own
    else:
        # For regular users, exclude private and admin-only
        lessonplans = lessonplans.exclude(visibility__in=['private', 'admin'])
    
    context = {
        'profile_teacher': teacher,
        'lessonplans': lessonplans.select_related('subject', 'class_level'),
    }
    return render(request, 'lessonplans/teacher_profile.html', context)