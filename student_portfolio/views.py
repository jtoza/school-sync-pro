from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from .models import PortfolioItem, PortfolioCategory
from .forms import PortfolioItemForm

class PortfolioListView(LoginRequiredMixin, ListView):
    model = PortfolioItem
    template_name = 'student_portfolio/portfolio_list.html'
    context_object_name = 'portfolio_items'
    
    def get_queryset(self):
        # Students see only their items, staff see all
        if hasattr(self.request.user, 'student'):
            return PortfolioItem.objects.filter(student=self.request.user.student, is_published=True)
        return PortfolioItem.objects.filter(is_published=True)

class PortfolioDetailView(LoginRequiredMixin, DetailView):
    model = PortfolioItem
    template_name = 'student_portfolio/portfolio_detail.html'
    context_object_name = 'item'

class PortfolioCreateView(LoginRequiredMixin, CreateView):
    model = PortfolioItem
    form_class = PortfolioItemForm
    template_name = 'student_portfolio/portfolio_form.html'
    success_url = reverse_lazy('student_portfolio:portfolio_list')
    
    def form_valid(self, form):
        form.instance.student = self.request.user.student
        return super().form_valid(form)

class PortfolioUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = PortfolioItem
    form_class = PortfolioItemForm
    template_name = 'student_portfolio/portfolio_form.html'
    success_url = reverse_lazy('student_portfolio:portfolio_list')
    
    def test_func(self):
        portfolio_item = self.get_object()
        return self.request.user.student == portfolio_item.student

class PortfolioDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PortfolioItem
    template_name = 'student_portfolio/portfolio_confirm_delete.html'
    success_url = reverse_lazy('student_portfolio:portfolio_list')
    
    def test_func(self):
        portfolio_item = self.get_object()
        return self.request.user.student == portfolio_item.student

# Public view for sharing (no login required)
class PublicPortfolioView(DetailView):
    model = PortfolioItem
    template_name = 'student_portfolio/portfolio_public.html'
    context_object_name = 'item'
    
    def get_queryset(self):
        return PortfolioItem.objects.filter(is_published=True)