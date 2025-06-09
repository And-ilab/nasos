from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string

from .forms import UserForm, UserFormUpdate
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from .models import User, ActivityLog


def archive_view(request):
    users = User.objects.filter(role='student')
    return render(request, 'admin_panel/archive.html', {'users': users})

def get_user_details(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    details_html = render_to_string('admin_panel/user_details.html', {'user': user})
    extra_info_html = render_to_string('admin_panel/user_extra_info.html', {'user': user})
    return JsonResponse({
        'details': details_html,
        'extra_info': extra_info_html,
    })


def archive_user(request, user_type, user_id):
    """Archive a user instead of deleting."""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.is_archived = True
        user.save()
        messages.success(request, f'Пользователь {user.username} перемещен в архив.')
        return redirect('chat_dashboard:user_list')

    return redirect('admin_panel:user_list')


def user_list(request):
    search_query = request.GET.get('search', '')
    sort_column = request.GET.get('sort', 'username')
    page_number = request.GET.get('page', 1)
    archive_filter = request.GET.get('archive_filter', 'all')

    print(archive_filter)

    users = User.objects.all()

    if archive_filter == 'active':
        users = users.filter(is_archived=False)
    elif archive_filter == 'archived':
        users = users.filter(is_archived=True)
    # Для 'all' - оставляем всех пользователей без фильтрации

    combined_users = []
    for user in users:
        combined_users.append({
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'middle_name': user.middle_name,
            'username': user.username,
            'group_number': user.group_number,
            'role': user.get_role_display(),
            'test': user.test,
            'date_of_the_test': user.date_of_the_test,
            'time_test': user.time_test,
            'scores': user.scores,
        })

    # Фильтрация по поисковому запросу
    if search_query:
        combined_users = [
            u for u in combined_users
            if (search_query.lower() in u['first_name'].lower() or
                search_query.lower() in u['last_name'].lower() or
                search_query.lower() in u['group_number'].lower() or
                search_query.lower() in u['username'].lower())
        ]

    reverse_sort = sort_column.startswith('-')
    sort_key = sort_column.lstrip('-') if reverse_sort else sort_column

    combined_users.sort(
        key=lambda x: str(x.get(sort_key, '')).lower(),
        reverse=reverse_sort
    )

    paginator = Paginator(combined_users, 10)
    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)

    return render(request, 'admin_panel/users.html', {
        'page_obj': page_obj,
        'sort_column': sort_column,
        'search_query': search_query,
        'archive_filter': archive_filter  # Передаём текущий фильтр в шаблон
    })


def user_create(request):
    """Creates a new user."""
    form = UserForm(request.POST or None)
    user = request.user
    username = user.username
    if request.method == 'POST':
        username = request.POST.get('username')
        if User.objects.filter(username=username).exists():
            return render(request, 'admin_panel/user_create_form.html', {
                'form': form,
                'email_exists': True,
                'username': username
            })

        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            messages.success(request,
                             "Создана новая учетная запись. Данные для её активации направлены на указанный вами электронный адрес.")
            return redirect('admin_panel:user_list')  # Перенаправляем на список пользователей

    return render(request, 'admin_panel/user_create_form.html', {'form': form})


def index(request):
    return render(request, "admin_panel/index.html")


def user_update(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        form = UserFormUpdate(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            user.save()
            return redirect('admin_panel:user_list')
    else:
        form = UserFormUpdate(instance=user)

    return render(request, 'admin_panel/user_update_form.html', {
        'form': form,
    })


def user_delete(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == 'POST':
        user.delete()
        return redirect('admin_panel:user_list')

    return render(request, 'admin_panel/user_delete_form.html', {
        'user': user,
    })


def analytics(request):
    user = request.user
    return render(request, 'admin_panel/analytics.html')

#
# def user_test(request):
#     return render(request, 'admin_panel/analytics.html')

def user_test_view(request):
    students = User.objects.filter(role='student')
    return render(request, 'admin_panel/user_test.html', {'students': students})

def start_theory_test(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        student = User.objects.get(id=student_id)

        ActivityLog.objects.create(user=student, action='start_theory')

        # логика запуска теста
        return redirect('admin_panel:user_list')
    return redirect('admin_panel:user_test')

def start_practice_test(request):
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        difficulty = request.POST.get('difficulty')  # 'easy', 'medium', 'hard'
        student = User.objects.get(id=student_id)

        ActivityLog.objects.create(
            user=student,
            action='start_practice',
            difficulty=difficulty
        )

        # логика запуска практического теста с уровнем сложности
        # например, можно student.time_test = время_в_зависимости_от_difficulty

        return redirect('admin_panel:user_list')
    return redirect('admin_panel:user_test')

def activity_log_view(request):
    logs = ActivityLog.objects.select_related('user').order_by('-timestamp')
    return render(request, 'admin_panel/activity_log.html', {'logs': logs})