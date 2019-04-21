from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('event/choices/<int:pk>/', views.event_join, name='event_join'),
    path('event/close/<int:pk>/', views.event_close, name='event_close'),
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('event/new/', views.event_new, name='event_new'),
    path('event/', views.event_list, name='event_list'),
    path('event/<int:pk>/', views.event_detail, name='event_detail'),
    path('event/<int:pk>/result', views.result, name='result'),
    path('poll/<int:pk>/result', views.result_poll, name='result_poll'),
    path('poll/close/<int:pk>/', views.poll_close, name='poll_close'),
    path('poll/submit/', views.poll_submit, name='poll_submit'),
    path('event/submit/', views.event_submit, name='event_submit'),
    path('poll/new', views.poll_new, name='poll_new'),
    path('poll/', views.poll_list, name='poll_list'),
    path('poll/<int:pk>/', views.poll_detail, name='poll_detail'),
    path('poll/<int:pk>/update/', views.poll_update, name='poll_update'),
    path('event/<int:pk>/update/', views.event_update, name='event_update'),
    path('poll/private/', views.poll_list_private, name='poll_list_private'),
    path('more/<str:query>/', views.more, name='more'),
    path('profile/', views.user_profile, name='profile'),
    path('logout/', views.logout_deal, name='logout'),
    path('register/', views.register, name='register'),
    path('login/', views.login_deal, name='login'),
    path('update', views.profile, name='update'),
    path('change_password/', views.change_password, name='change_password'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='linkup/password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='linkup/password_reset_done.html'), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='linkup/password_reset_confirm.html'), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='linkup/password_reset_complete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
