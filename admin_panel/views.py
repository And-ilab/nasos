from datetime import timedelta

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from .forms import UserForm, UserFormUpdate
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.db.models import Q, Max
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from .models import User, ActivityLog

from django.http import JsonResponse
from django.db.models import Avg, Count, Case, When, IntegerField
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth



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
            #'test': user.test,
            #'date_of_the_test': user.date_of_the_test,
            #'time_test': user.time_test,
            #'scores': user.scores,
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
    students = User.objects.filter(role='student').annotate(
        last_activity=Max('activitylog__timestamp'),
        progress=Case(
            When(scores__gte=9, then=100),
            When(scores__gte=7, then=75),
            When(scores__gte=5, then=50),
            default=25,
            output_field=IntegerField()
        )
    )

    groups = User.objects.filter(role='student').values_list('group_number', flat=True).distinct()

    return render(request, 'admin_panel/analytics.html', {
        'students': students,
        'groups': [g for g in groups if g is not None]
    })


def analytics_data(request):
    report_type = request.GET.get('report_type', 'btn-learning-report')
    period = request.GET.get('period', 'month')
    group = request.GET.get('group', 'all')

    students = User.objects.filter(role='student')
    if group != 'all':
        students = students.filter(group_number=group)

    try:
        if report_type == 'btn-learning-report':
            data = prepare_learning_report(students, period)
        elif report_type == 'btn-testing-report':
            data = prepare_testing_report(students, period)
        elif report_type == 'btn-activity-report':
            data = prepare_activity_report(students, period)
        else:
            data = {'error': 'Invalid report type'}

        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def prepare_learning_report(students, period):
    date_trunc = {
        'day': TruncDay,
        'week': TruncWeek,
        'month': TruncMonth
    }.get(period, TruncMonth)

    results = students.annotate(
        period=date_trunc('last_activity'),
        score_group=Case(
            When(scores__gte=9, then=4),
            When(scores__gte=7, then=3),
            When(scores__gte=5, then=2),
            default=1,
            output_field=IntegerField()
        )
    ).values('period', 'score_group').annotate(count=Count('id'))

    labels = sorted({r['period'].strftime('%d.%m.%Y') for r in results})

    datasets = [
        {
            'label': 'Отлично (9-10)',
            'data': [next((r['count'] for r in results
                           if r['period'].strftime('%d.%m.%Y') == label and r['score_group'] == 4), 0)],
            'backgroundColor': '#4CAF50'
        },
        {
            'label': 'Хорошо (7-8)',
            'data': [next((r['count'] for r in results
                           if r['period'].strftime('%d.%m.%Y') == label and r['score_group'] == 3), 0)],
            'backgroundColor': '#8BC34A'
        },
        {
            'label': 'Удовлетворительно (5-6)',
            'data': [next((r['count'] for r in results
                           if r['period'].strftime('%d.%m.%Y') == label and r['score_group'] == 2), 0)],
            'backgroundColor': '#FFC107'
        },
        {
            'label': 'Неуд (0-4)',
            'data': [next((r['count'] for r in results
                           if r['period'].strftime('%d.%m.%Y') == label and r['score_group'] == 1), 0)],
            'backgroundColor': '#F44336'
        }
    ]

    return {'labels': labels, 'datasets': datasets}

def get_count(results, label, score_group):
    for r in results:
        if r['period'].strftime('%d.%m.%Y') == label and r['score_group'] == score_group:
            return r['count']
    return 0
#
def prepare_testing_report(students, period):
    # Заглушка - реализуйте аналогично prepare_learning_report
    return {
        'labels': ['Тест 1', 'Тест 2', 'Тест 3'],
        'datasets': [{
            'label': 'Результаты тестов',
            'data': [75, 60, 90],
            'backgroundColor': '#2196F3'
        }]
    }

def prepare_activity_report(students, period):
    # Заглушка - реализуйте аналогично prepare_learning_report
    return {
        'labels': ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'],
        'datasets': [{
            'label': 'Активность',
            'data': [120, 190, 90, 150, 200, 50, 30],
            'backgroundColor': '#9C27B0'
        }]
    }
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

@csrf_exempt
def get_activity_history(request, user_id):
    # Получаем последние 10 активностей пользователя
    activities = ActivityLog.objects.filter(user_id=user_id).order_by('-start_time')[:10]

    # Формируем список активностей в нужном формате
    activities_list = []
    for activity in activities:
        activities_list.append({
            'action': activity.action,
            'action_display': activity.get_action_display(),
            'start_time': activity.start_time.strftime('%d.%m.%Y %H:%M'),
            'end_time': activity.end_time.strftime('%d.%m.%Y %H:%M') if activity.end_time else None,
            'user_time': str(timedelta(seconds=activity.user_time)) if activity.user_time else None,
            'norm_time': str(timedelta(seconds=activity.norm_time)) if activity.norm_time else None,
            'score': activity.score,
        })

    # Возвращаем данные в формате JSON
    return JsonResponse({
        'status': 'success',
        'activities': activities_list
    }, encoder=DjangoJSONEncoder)

@csrf_exempt
def start_activity(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            activity_type = request.POST.get('activity_type')

            # Создаем запись о начале активности
            activity = ActivityLog.objects.create(
                user_id=user_id,
                action=activity_type,
                start_time=timezone.now()
            )

            return JsonResponse({
                'status': 'success',
                'activity_id': activity.id,
                'message': 'Активность начата'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Метод не разрешен'
    }, status=405)


@csrf_exempt
def end_activity(request):
    if request.method == 'POST':
        try:
            user_id = request.POST.get('user_id')
            activity_type = request.POST.get('activity_type')
            duration = int(request.POST.get('duration', 0))
            score = int(request.POST.get('score', 0))

            # Ищем последнюю НЕЗАВЕРШЕННУЮ активность (где start_time есть, а end_time=None)
            activity = ActivityLog.objects.filter(
                user_id=user_id,
                action=activity_type,
                end_time__isnull=True  # Изменено с end_time на end_time__isnull
            ).latest('start_time')

            # Обновляем запись
            activity.end_time = timezone.now()
            activity.user_time = duration
            activity.norm_time = 5400  # 1.5 часа в секундах
            activity.score = score
            activity.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Активность завершена'
            })
        except ActivityLog.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Не найдена активность для завершения'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=400)
    return JsonResponse({
        'status': 'error',
        'message': 'Метод не разрешен'
    }, status=405)