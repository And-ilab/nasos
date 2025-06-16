from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('archive/', views.archive_view, name='archive'),
    path('get_user_details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    # # path('archive/filter/', views.archive_filter_view, name='archive_filter'),
  #  path('analytics/', views.analytics, name='analytics'),
    path('get_user_details/<int:user_id>/', views.get_user_details, name='get_user_details'),
    path('users/', views.user_list, name='user_list'),
    path('test/', views.user_test_view, name='user_test'),
    path('start_theory/', views.start_theory_test, name='start_theory_test'),
    path('start_practice/', views.start_practice_test, name='start_practical_test'),
    path('user/create/', views.user_create, name='user_create'),
    path('user/update/<int:pk>/', views.user_update, name='user_update'),
    path('user/delete/<int:pk>/', views.user_delete, name='user_delete'),
    # path('users/update/<str:user_type>/<int:pk>/', views.user_update, name='user_update'),
    # path('users/delete/<str:user_type>/<int:pk>/', views.user_delete, name='user_delete'),
    # path('users/archive/<str:user_type>/<int:user_id>/', views.archive_user, name='archive_user'),
    # path('users/restore/<str:user_type>/<int:user_id>/', views.restore_user, name='restore_user'),
    path('', views.index, name='index'),
    path('activity_log/', views.activity_log_view, name='activity_log'),
    path('start_activity/', views.start_activity, name='start_activity'),
    path('end_activity/', views.end_activity, name='end_activity'),
    path('get_activity_history/<int:user_id>/', views.get_activity_history, name='get_activity_history'),
    #path('analytics/', views.analytics_data, name='analytics_data'),
    path('analytics/', views.analytics, name='analytics'),
    path('api/analytics/', views.analytics_data, name='analytics_data'),

]
