"""

""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
Purpose: in this urls module we created urls for all rest api in views and this will included in main url module
author:  Sachin Shrikant Jadhav
since :  25-09-2019
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

"""

from django.conf.urls import url
from django.urls import path

from . import views

urlpatterns = [
    url(r'^register/$', views.User_Create.as_view(), name='register'),
<<<<<<< HEAD
    path('send_email/', views.Reset_Passward.as_view(), name='reset_passward'),
    path('set_new_password/<userReset>', views.Resetpassword.as_view(), name='resetpassword'),
    path('hello/', views.HelloView.as_view(), name='hello'),
=======
    path('sendemail/', views.Reset_Passward.as_view(), name='reset_passward'),
    path('setnewpassword/<userReset>', views.Resetpassword.as_view(), name='resetpassword'),
    # path('hello/', views.HelloView.as_view(), name='hello'),
>>>>>>> b2154c4e... code coverage done
    path('logout/', views.Logout.as_view(), name='logout'),
    path('upload_profile/', views.S3Upload.as_view(), name='upload_profile'),
    path('login/', views.Login.as_view(), name='users'),
    path('r/<str:id>/', views.reset_password, name='reset_password'),
    path('a/<str:short_id>/', views.activate, name='activate'),
    path('read_profile/<str:bucket>/<str:object_name>/', views.s3_read, name='read_profile'),
]
