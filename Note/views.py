import json
from Services import redis
import pickle
import logging
from rest_framework.validators import UniqueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import render, redirect
# Create your views here.
from rest_framework.generics import GenericAPIView
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Note, Label
from Note.serializers import NoteSerializers, LabelSerializers
from utils import Smd_Response
from users.decoraters import login_required
from django.contrib.auth.models import User
from .service.note import Label_And_Note_Validator

logger = logging.getLogger(__name__)


class Note_Create(GenericAPIView):
    serializer_class = NoteSerializers

    # permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """

        :param request:user request for create a note
        :return:this function is used for create new note and save

        """

        try:
            collaborator = request.data['collaborator']
            pin = request.data['is_pin']
            trash = request.data['is_trash']
            archive = request.data['is_archive']
            label = request.data['label']
            note = request.data['note']
            title = request.data['title']
            image = request.data['image']
            user = request.data['user']
            validate_label = Label_And_Note_Validator().validate_label(label)
            if not validate_label['success']:
                return HttpResponse(json.dumps(validate_label), status=400)
            validate_collaborator = Label_And_Note_Validator().validate_collaborator(collaborator)
            if not validate_collaborator['success']:
                return HttpResponse(json.dumps(validate_collaborator), status=400)
            note_create = Note.objects.create(user_id=user, title=title, note=note, is_pin=pin,
                                              image=image, is_trash=trash, is_archive=archive)
            if validate_label['success'] == True:
                for labels in validate_label:
                    note_create.collaborator.add(labels)
            if validate_collaborator['success'] == True:
                for collaborators in validate_collaborator:
                    note_create.label.add(collaborators)

            redis.Del(user)
            smd = Smd_Response(True, 'successfully note created', status_code=200)
        except Exception:
            smd = Smd_Response()
            logger.warning('something was wrong warning from Note.views.note_api')
        return smd


# class Share_Note(GenericAPIView):
#
#     def get(self, request, note_id, provider, *args, **kwargs):
#         """
#         :param request:user request for share a note
#         :param note_id:here we get note id for share a note
#         :param provider:here we get provider for share a note
#         :return:this function is used for share a specific note
#         """
#         try:
#             note = Note.objects.get(pk=int(note_id))
#             if provider == 'twitter':
#                 url = 'https://twitter.com/intent/tweet?text=' + note.note
#                 return redirect(url)
#             elif provider == 'reddit':
#                 url = 'https://www.reddit.com/submit?title=' + note.note
#                 return redirect(url)
#             else:
#                 smd = Smd_Response(False, 'please provide twitter or reddit provider for share a note', [])
#         except Note.DoesNotExist:
#             smd = Smd_Response(False, 'please provide valid note_id', [])
#         except ValueError:
#             smd = Smd_Response(False, 'please provide note_id in number', [])
#         except Exception:
#             smd = Smd_Response()
#         return smd


class Note_Crud(GenericAPIView):
    serializer_class = NoteSerializers

    # permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser,)

    def put(self, request, note_id, *args, **kwargs):

        try:
            # uu = request.data
            # uu=request.body
            # hh = uu.dict()
            # print(hh)
            # myDict = dict(uu.iterlists())
            # print(myDict)
            # print(request.data)
            yu = json.loads(request.body)
            print(yu)
            if "collaborator" in yu:
                # klist = []
                tt = yu['collaborator']
                yuu = Label_And_Note_Validator().putvalid(tt)
                # for i in tt:
                #     user_obj = User.objects.get(email=i)
                #     klist.append(user_obj.id)
                #     print(user_obj.username)
                yu['collaborator'] = yuu
            # if "label" in yu:
            #     tt = yu['label']
            #     # for i in tt:
            #     #     label_obj = Label.objects.get(name=i)
            #     #     llist.append(label_obj.id)
            #     yy = Label_And_Note_Validator().labelvalid(tt)
            #     yu["label"] = yy

            update_note = Note.objects.get(pk=note_id)
            # print(update_note)
            # print(yu)
            # print(yu)
            serializer = NoteSerializers(instance=update_note, data=yu, partial=True)
            if serializer.is_valid():
                print('gggg')
                serializer.save()
                #     smd = Smd_Response(True, 'dhdhdshss')
                # else:
                #     smd = Smd_Response(False, 'dhdhdshss')

            # collaborator = request.data['collaborator']
            # pin = request.data['is_pin']
            # trash = request.data['is_trash']
            # archive = request.data['is_archive']
            # label = request.data['label']
            # note = request.data['note']
            # title = request.data['title']
            # image = request.data['image']
            # user = request.data['user']
            # if len(label) != 0:
            #     new_label = Label.objects.get(name=label)
            #     if new_label:
            #         add_label = new_label
            #     else:
            #         return Response('not valid note')
            # else:
            #     is_label = False
            #
            # if len(collaborator) != 0:
            #     new_collaborator = User.objects.get(email=collaborator)
            #     if new_collaborator:
            #         add_collaborator = new_collaborator
            #     else:
            #         return Response('not valid user')
            # else:
            #     is_collaborator = False
            #
            # update_note.is_pin = pin
            # update_note.is_trash = trash
            # update_note.is_archive = archive
            # update_note.note = note
            # update_note.title = title
            # update_note.image = image
            # if is_collaborator:
            #     update_note.collaborator.add(add_label)
            # if is_label:
            #     update_note.label.add(add_collaborator)
            # user = request.user
            # redis.Del(user.id)
            # smd = Smd_Response(True, 'successfully note updated', status_code=200)
            # return Response(smd)
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'your label is not valid please add label and try')
        except User.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid collaborator')
        except KeyError:
            smd = Smd_Response(False, 'please enter valid label input ')
        # except Exception:
        #     smd = Smd_Response()
        #     logger.warning('something was wrong warning from Note.views.note_api')
        return smd

    def delete(self, request, note_id, *args, **kwargs):
        try:

            Note.objects.get(pk=note_id).delete()
            user = request.user
            redis.Del(user.id)
            smd = Smd_Response(False, 'note deleted successfully', status_code=200)
        except Note.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid note_id')
        except Exception:
            smd = Smd_Response()
        return smd


class Get_All_Note(GenericAPIView):

    def get(self, request, user_id, *args, **kwargs):
        try:
            data = redis.Get(user_id)
            if data:
                hh = pickle.loads(data)
                serializer = NoteSerializers(hh, many=True)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                return smd
            data = Note.objects.filter(user_id=user_id)
            if data:
                serializer = NoteSerializers(data, many=True)
                fg = pickle.dumps(data)
                redis.Set(user_id, fg)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
            else:
                smd = Smd_Response(False, 'please enter valid user id')
        except Note.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid user for get a note')
        except Exception:
            smd = Smd_Response()
        return smd


class Label_Create(GenericAPIView):
    serializer_class = LabelSerializers

    # permission_classes = (IsAuthenticated,)
    def post(self, request, *args, **kwargs):
        """
        :param request:user request for create a note
        :return:this function is used for create new note and save
        """
        try:
            serializer = LabelSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save()
                user = serializer.data['user']
                redis.Del(str(user) + 'label')
                smd = Smd_Response(True, 'label successfully created', status_code=200)
                logger.warning('label created')
            else:
                smd = Smd_Response(False, serializer.errors)
                logger.warning('not valid input warning from Note.views.Label_api')
        except Exception:
            smd = Smd_Response()
            logger.warning('something was wrong warning from Note.views.Label_api')
        return smd


class Label_Crud(GenericAPIView):
    serializer_class = LabelSerializers
    authentication_classes = (IsAuthenticated,)

    def put(self, request, label_id, *args, **kwargs):
        try:
            user = request.data['user']
            label = Label.objects.get(pk=label_id, user_id=user)
            if label:
                label.name = request.data['name']
                label.save()
                redis.Del(str(user) + 'label')
                smd = Smd_Response(True, 'label updated successfully', status_code=200)
            else:
                smd = Smd_Response(False, 'please enter valid label id or user id ')
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid label id or user id ')
        except Exception:
            smd = Smd_Response()
        return smd

    def delete(self, request, label_id, *args, **kwargs):
        try:
            Label.objects.get(pk=label_id).delete()
            user = request.user
            redis.Del(str(user.id) + 'label')
            smd = Smd_Response(False, 'label deleted successfully', status_code=200)
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid label_id ')
        except Exception:
            smd = Smd_Response()
        return smd


class Get_Label(GenericAPIView):

    def get(self, request, user_id, *args, **kwargs):
        try:
            data = redis.Get(str(user_id) + 'label')
            if data:
                hh = pickle.loads(data)
                serializer = LabelSerializers(hh, many=True)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                return smd
            label = Label.objects.filter(user_id=user_id)
            if label:
                serializer = LabelSerializers(label, many=True)
                fg = pickle.dumps(label)
                redis.Set(str(user_id) + 'label', fg)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
            else:
                smd = Smd_Response(False, 'not valid user id please enter valid user_id')
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'for this user id label not available please enter valid user_id')
        except Exception:
            smd = Smd_Response()
        return smd
