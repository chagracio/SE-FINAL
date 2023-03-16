from django.urls import path
from . import views
urlpatterns = [
    path('login_user', views.login_user, name="login"),
    path('signup_user', views.signup_user, name="signup"),
    path('logout_user', views.logout_user, name="logout"),
    path('terms', views.terms, name="TermsConditions"),
]