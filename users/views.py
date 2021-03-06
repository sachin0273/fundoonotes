"""

**************************************************************************************************

Purpose: in this views module we created rest_api for user users ,register,forgot_password
author:  Sachin Shrikant Jadhav
since :  25-09-2019

**************************************************************************************************

"""
import pdb
import re
from urllib.parse import unquote
from rest_framework import status
from rest_framework.response import Response
from social.apps.django_app.utils import load_backend
from social.apps.django_app.utils import load_strategy
from social.backends.oauth import BaseOAuth1, BaseOAuth2
from social.exceptions import AuthAlreadyAssociated
import requests
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect, render
import json
import jwt
from django.contrib.auth import authenticate, get_user_model
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from jwt import DecodeError
from rest_framework import status, generics
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from Lib import redis
from users.decoraters import login_required
# from users.models import Profile
# from users.models import Profile
from .serializers import UserSerializer, EmailSerializer, PasswordSerializer, LoginSerializer, ImageSerializer
from Lib.pyjwt_token import Jwt
from rest_framework.permissions import IsAuthenticated
from Lib.event_emmiter import email_event
from Lib.amazons3 import AmazonS3
import logging
from utils import validate_email, build_url
from urlshortening.models import get_short_url, Url
from utils import Smd_Response
from django.urls import reverse

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCreate(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        """

        :purpose: in this function we register a new user via sending jwt token on email
        :param request: here we get post request
        :return:in this function we take user input for registration and sent mail to email id

        """

        try:
            # pdb.set_trace()
            serializer = UserSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                user.is_active = False
                user.save()
                if user:
                    payload = {
                        'username': self.request.data['username'],
                        'email': self.request.data['email'],
                    }
                    token = Jwt().register_token(payload)
                    long_url = reverse('activate', args=[token])
                    short_url = get_short_url(long_url)  # Url object
                    message = render_to_string('users/token.html', {
                        'name': user.username,
                        'domain': get_current_site(request).domain,
                        'url': short_url.short_id
                    })
                    recipient_list = [self.request.data['email'], ]
                    response = Smd_Response(True, 'you registered successfully for activate your account please check '
                                                  'your email', status_code=200)
                    email_event.emit("account_activate_event", message, recipient_list)
                    return response
                response = Smd_Response(False, 'you are not validated try again', [])
                return response
            logger.warning('not valid input warning from users.views.register_api')
            return Smd_Response(message=serializer.errors)
        except Exception as e:
            logger.warning('something was wrong ' + str(e))
            smd = Smd_Response()
        return smd


class Login(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        """

        :param request: here we get post request
        :return:this is users api view for user users after users its generate the token

        """
        try:
            if not "username" in request.data and not "password" in request.data:
                raise KeyError("username or password is missing")
            if not 'username' in request.data:
                raise KeyError('username is missing')
            if not 'password' in request.data:
                raise KeyError('password is missing')
            username = request.data["username"]
            password = request.data["password"]
            print(username)
            if username == "" and password == "":
                raise KeyError("username and password is not be blank ")
            if username == "":
                raise KeyError('username is required')
            if password == "":
                raise KeyError('password is required')
            user = authenticate(username=username, password=password)
            if user:
                payload = {
                    'username': username,
                    'password': password,
                }
                token = Jwt().login_token(payload)
                redis.Set(user.id, token)
                smd = {"success": True, "message": "successful", "data": token}
                logger.info('successfully logged in info from users.views.login_api')
                return HttpResponse(json.dumps(smd))
            else:
                logger.warning('not valid user warning from users.views.login_api')
                smd = Smd_Response(False, 'please provide valid credentials', [])
        except KeyError as error:
            print(error)
            logger.warning('any one input field is blank warning from users.views.login_api')
            logger.error('any one input field is blank' + str(error))
            smd = Smd_Response(False, str(error), [])
        except Exception as e:
            logger.error('something is wrong warning' + str(e))
            smd = Smd_Response()
        return smd


def activate(request, short_id, *args, **kwargs):
    """

    :param request: here we use get request
    :param short_id:in this id we gate token
    :return:in this function we get tokan when user click the link and we decode the token and
            activate the user

    """
    smd = {'success': False,
           'Message': 'account activation failed',
           'Data': []}
    try:
        url = Url.objects.get(short_id=short_id)
        if url is None:
            raise KeyError

        token = url.url.split('/')

        try:
            decodedPayload = jwt.decode(token[2], "SECRET_KEY")
        except DecodeError:
            return HttpResponse(json.dumps(smd))

        username = decodedPayload["username"]
        email = decodedPayload["email"]
        user = User.objects.get(username=username, email=email)
        if user:
            user.is_active = True
            user.save()
            smd['success'] = True
            smd['Message'] = 'account activated successfully'
            return HttpResponse(json.dumps(smd))
        else:
            return HttpResponse(json.dumps(smd))
    except ObjectDoesNotExist:
        HttpResponse(json.dumps(smd))
    except KeyError:
        HttpResponse(json.dumps(smd))
    except Exception:
        return HttpResponse(json.dumps(smd))


class Reset_Passward(GenericAPIView):
    serializer_class = EmailSerializer

    def post(self, request, *args, **kwargs):
        """
        :param request: here is post request por set password
        :return: in this function we take email from user and send toaken for verification
        """
        try:
            if not 'email' in request.data:
                raise KeyError('email is missing')
            email = request.data['email']
            print(email)
            if email == "":
                raise KeyError('email field not be blank')
            if not validate_email(email):
                raise ValueError
            user = User.objects.get(email=email)
            if user:
                payload = {
                    'username': user.username,
                    'email': user.email,
                }
                token = Jwt().register_token(payload)
                long_url = reverse('reset_password', args=[token])
                short_url = get_short_url(long_url)  # Url object
                message = render_to_string('users/email_template.html', {
                    'name': user.username,
                    'domain': get_current_site(request).domain,
                    'url': short_url.short_id
                })
                recipient_list = [user.email, ]
                email_event.emit("reset_password_event", message, recipient_list)
                smd = Smd_Response(True, 'you"re email is verified for reset password check you"re email',
                                   status_code=200)
                return smd
            else:
                smd = Smd_Response(False, 'you are not valid user register first', [])
                logger.warning('not valid user warning from users.views.Reset_password_api')
        except ObjectDoesNotExist as e:
            logger.warning('email not registered' + str(e))
            smd = Smd_Response(False, 'this email id not registered', [])
        except ValueError as e:
            smd = Smd_Response(False, 'please provide valid email address', [])
            logger.warning('not valid email address' + str(e))
        except KeyError as error:
            smd = Smd_Response(False, str(error), [])
            logger.warning('input is blank ' + str(error))
        except Exception as e:
            logger.warning('something is wrong ' + str(e))
            smd = Smd_Response()
        return smd


def reset_password(request, id):
    """
    :param request: request for reset password
    :param id: here we token for decoding
    :return:this function used for reset password
    """
    smd = {'success': False,
           'Message': 'you are not valid user',
           'Data': []}
    try:
        try:
            url = Url.objects.get(short_id=id)
            token = url.url.split('/')
            decode = jwt.decode(token[2], "SECRET_KEY")
        except DecodeError:
            smd['Message'] = 'token is invalid'
            return Response(smd)
        username = decode['username']
        user = User.objects.get(username=username)

        # if user is not none then we will redirect to the reset password page
        if user is not None:
            return redirect(reverse('resetpassword', args=[str(user)]))
        else:
            return Response(smd)
    except ObjectDoesNotExist:
        smd['Message'] = 'please provide valid credential'
        return Response(smd)
    except Exception:
        smd['Message'] = 'something was wrong try again'
        return Response(smd)


class Resetpassword(GenericAPIView):
    serializer_class = PasswordSerializer

    def post(self, request, userReset, *args, **kwargs):

        smd = {'success': False,
               'Message': 'please enter valid password',
               'Data': []}
        try:
            if not 'password' in request.data and not 'confirm_password' in request.data:
                raise KeyError('password and confirm password is missing')
            if not 'password' in request.data:
                raise KeyError('password is missing')
            if not 'confirm_password' in request.data:
                raise KeyError('confirm password is missing')
            password = request.data['password']
            confirm_password = request.data['confirm_password']
            # here we will save the user password in the database
            if password == "" and confirm_password == "":
                raise KeyError('password and confirm password may not be blank')
            if password == "":
                raise KeyError('password field may not be blank')
            if confirm_password == "":
                raise KeyError('confirm password field may not be blank')
            if password != confirm_password:
                smd['Message'] = 'password not match'
                return Response(smd)
            else:
                user = User.objects.get(username=userReset)
                user.set_password(password)
                # here we will save the user password in the database
                user.save()
                smd['success'] = True
                smd['Message'] = 'password changed successfully'
                return Response(smd)

        except ObjectDoesNotExist:
            smd['Message'] = 'not valid credentials try again'
            return Response(smd)
        except KeyError as error:
            smd['Message'] = str(error)
            return Response(smd)
        except Exception:
            smd['Message'] = 'something was wrong try again'
            return Response(smd)


@method_decorator(login_required, name='dispatch')
class Logout(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            user = request.user
            redis.Del(user.id)
            smd = Smd_Response(True, 'safely logged out', [])
        except Exception:
            smd = Smd_Response()
        return smd


# class ProfileUpload(GenericAPIView):
#     serializer_class = ImageSerializer
#
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request, *args, **kwargs):
#         """
#
#         :param request: here we using post request for uploading photo
#         :return: this function is used for upload a photo on amazon s3
#
#         """
#         try:
#             serializer = ImageSerializer(data=request.data)
#             if serializer.is_valid():
#                 image = request.data['image']
#                 user = request.user
#                 print(user.id)
#                 exist_image = Profile.objects.get(user_id=user.id)
#                 if exist_image:
#                     url = AmazonS3().upload_file(image, object_name=user.username)
#                     exist_image.image = url
#                     exist_image.save()
#                     smd = Smd_Response(True, 'image uploaded successfully')
#                 else:
#                     url = AmazonS3().upload_file(image, object_name=user.username)
#                     Profile.objects.create(image=url, user_id=user.id)
#                     smd = Smd_Response(True, 'image uploaded successfully')
#             else:
#                 smd = Smd_Response(False, 'please provide valid image', [])
#                 logger.warning('not a valid image warning from users.views.s3upload_api')
#         except Exception:
#             logger.warning('something is wrong warning from users.views.s3upload_api')
#             smd = Smd_Response()
#         return smd
#
#
# def read_profile(request, bucket, object_name, *args, **kwargs):
#     """
#
#     :param bucket:here we taking bucket name from path parameter
#     :param object_name: here we taking object name from parameter
#     :return:this function is used for generate preassigned url for view photo
#
#     """
#     try:
#         url = settings.s3.generate_presigned_url(
#             ClientMethod='get_object',
#             Params={
#                 'Bucket': bucket,
#                 'Key': object_name
#             }
#         )
#         print(url)
#         return redirect(url)
#     except Exception:
#         smd = Smd_Response()
#         return smd


def social_login(request):
    """

    :param request: here request means rendering the page
    :return:this function is used for render to the social login html page

    """
    return render(request, 'users/social_login.html')


def access_token(request):
    """

    :param request: here we get code from google oauth2
    :return:in this function using the code from the google get access token by using that token we get user information
           after that we create that user and successfully logged in user
    """
    try:
        path = request.get_full_path()
        code_path = path.split('&')
        code = code_path[0].split('=')
        code = unquote(code[1])
        print(code)

        url = settings.GOOGLE_ACCESS_TOKEN_URI
        data = {
            "code": code,
            "client_id": settings.GOOGLE_OAUTH2_KEY,
            "client_secret": settings.GOOGLE_OAUTH2_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI
        }
        response = requests.post(url, data)
        url = settings.GOOGLE_AUTH
        print(response.text)
        user_create = requests.post(url, response.json())
        print(user_create.status_code)
        if user_create.status_code == 201:
            return redirect(settings.BASE_URL)
        else:
            smd = Smd_Response(message='social user is not created')
    except Exception:
        smd = Smd_Response()
    return smd


class SocialSignUp(APIView):
    """
    in this class we used post function to create user for social login
    """

    def post(self, request, *args, **kwargs):
        """

        :param request:here we get post request with access token
        :return:this function use that access token and authenticate with backend and create a user
                and return response code 201 for created

        """
        try:
            provider = 'google-oauth2'
            authed_user = request.user if not request.user.is_anonymous else None

            strategy = load_strategy(request)

            backend = load_backend(strategy=strategy, name=provider, redirect_uri=None)

            if isinstance(backend, BaseOAuth1):

                token = {
                    'oauth_token': request.data['access_token'],
                    'oauth_token_secret': request.data['access_token_secret'],
                }
            elif isinstance(backend, BaseOAuth2):

                token = request.data['access_token']
            try:
                user = backend.do_auth(token, user=authed_user)
            except AuthAlreadyAssociated:

                return Response({"errors": "That social media account is already in use"},
                                status=status.HTTP_400_BAD_REQUEST)

            if user and user.is_active:
                return Response('logged in', status=status.HTTP_201_CREATED)
            else:
                return Response({"errors": "Error with social authentication"},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            smd = Smd_Response()
            return smd
