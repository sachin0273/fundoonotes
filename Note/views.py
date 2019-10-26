import json
from Lib import redis
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
from .service.note import Label_And_Note_Validator, Listing_Pages, update_redis, label_update_in_redis

logger = logging.getLogger(__name__)


class CreateAndGetNote(GenericAPIView):
    serializer_class = NoteSerializers

    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """

        :param request:user request for create a note
        :return:this function is used for create new note and save

        """

        try:
            collaborator = request.data['collaborator']
            pin = request.data['is_pin']
            archive = request.data['is_archive']
            label = request.data['label']
            note = request.data['note']
            title = request.data['title']
            image = request.data['image']
            user = request.user
            validate_label = Label_And_Note_Validator().validate_label(label)
            if not validate_label['success']:
                return HttpResponse(json.dumps(validate_label), status=400)
            validate_collaborator = Label_And_Note_Validator().validate_collaborator(collaborator)
            if not validate_collaborator['success']:
                return HttpResponse(json.dumps(validate_collaborator), status=400)
            note_create = Note.objects.create(user_id=user.id, title=title, note=note, is_pin=pin,
                                              image=image, is_archive=archive)

            if validate_label['success'] == True:
                for labels in validate_label['data']:
                    note_create.label.add(labels)

            if validate_collaborator['success'] == True:
                for collaborators in validate_collaborator['data']:
                    note_create.collaborator.add(collaborators)

            update_redis(user)
            logger.info('note created successfully')
            smd = Smd_Response(True, 'successfully note created', status_code=200)
        except Exception:
            smd = Smd_Response()
            logger.error('something was wrong error from Note.views')
        return smd

    def get(self, request, *args, **kwargs):
        """

        :param request:user request for get all notes
        :return: this function perform get operation of notes

        """
        try:
            user = request.user
            note_data = redis.Get(user.username)
            if note_data:
                notes = pickle.loads(note_data)
                serializer = NoteSerializers(notes, many=True)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('successfully get notes from redis')
                return smd
            all_notes = Note.objects.filter(user_id=int(user.id), is_trash=False, is_archive=False)
            if all_notes:
                serializer = NoteSerializers(all_notes, many=True)
                note = pickle.dumps(all_notes)
                redis.Set(user.username, note)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('successfully get notes from database')
            else:
                smd = Smd_Response(False, 'please enter valid user id')
        except Note.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid user for get a note')
            logger.error('note not exist for this note id error from Note.views')
        except ValueError:
            smd = Smd_Response(False, 'please enter user_id in digits')
        except Exception:
            logger.error('exception occurred while getting all notes error from Note.views')
            smd = Smd_Response()
        return smd


# classs Share_Note(GenericAPIView):
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


class UpdateAndDeleteNote(GenericAPIView):
    serializer_class = NoteSerializers

    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser,)

    def put(self, request, note_id, *args, **kwargs):
        """

        :param request: user request for put operation
        :param note_id: here we pass note id for specific update
        :return:this function used for update a note

        """

        try:
            request_data = json.loads(request.body)
            print(request_data['collaborator'])
            if "collaborator" in request_data:
                collaborators = request_data['collaborator']
                result = Label_And_Note_Validator().validate_collaborator_for_put(collaborators)
                if not result['success']:
                    return HttpResponse(json.dumps(result))
                request_data['collaborator'] = result['data']
            if "label" in request_data:
                labels = request_data['label']
                label_result = Label_And_Note_Validator().validate_label_for_put(labels)
                if not label_result['success']:
                    return HttpResponse(json.dumps(label_result))
                request_data['label'] = label_result['data']
            update_note = Note.objects.get(pk=int(note_id))
            serializer = NoteSerializers(instance=update_note, data=request_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                user = request.user
                update_redis(user)
                smd = Smd_Response(True, 'successfully note updated', status_code=200)
                logger.info('successfully note updated')
            else:
                smd = Smd_Response(False, serializer.errors)
        except Exception:
            smd = Smd_Response()
            logger.error('something was wrong error from Note.views')
        return smd

    def delete(self, request, note_id, *args, **kwargs):
        """

        :param request: user request for delete note
        :param note_id:here we pass note id for specific delete
        :return:this function used for perform delete operation of note

        """
        try:
            Note.objects.get(pk=int(note_id)).delete()
            user = request.user
            update_redis(user)
            smd = Smd_Response(False, 'note deleted successfully', status_code=200)
            logger.info('note deleted successfully')
        except Note.DoesNotExist:
            logger.error('note does not exist for this note id error from Note.views')
            smd = Smd_Response(False, 'please enter valid note_id')
        except ValueError:
            smd = Smd_Response(False, 'please enter note_id in digits')
        except Exception:
            logger.error('parent exception occurred error from Note.views')
            smd = Smd_Response()
        return smd


class CreateAndGetLabel(GenericAPIView):
    serializer_class = LabelSerializers

    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        """

        :param request:user request for create a note
        :return:this function is used for create new note and save

        """
        try:
            serializer = LabelSerializers(data=request.data)
            if serializer.is_valid():
                serializer.save(user=request.user)
                smd = Smd_Response(True, 'label successfully created', status_code=200)
                logger.info('successfully label created')
            else:
                smd = Smd_Response(False, serializer.errors)
                logger.warning('not valid input warning from Note.views')
        except Exception:
            smd = Smd_Response()
            logger.error('something was wrong warning from Note.views')
        return smd

    def get(self, request, *args, **kwargs):
        """

        :param request:user request for get all labels
        :return: this function perform get operation of labels

        """
        try:
            user = request.user
            data = redis.Get(user.username + 'label')
            if data:
                labels = pickle.loads(data)
                serializer = LabelSerializers(labels, many=True)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('all labels get successfully from redis')
                return smd
            label = Label.objects.filter(user_id=int(user.id))
            if label:
                serializer = LabelSerializers(label, many=True)
                all_label = pickle.dumps(label)
                redis.Set(user.username + 'label', all_label)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('all label get from database')
            else:
                smd = Smd_Response(False, 'not valid user id please enter valid user_id')
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'for this user id label not available please enter valid user_id')
            logger.error('for this user id label not exist error from Note.views.get_label')
        except ValueError:
            smd = Smd_Response(False, 'please enter user id in digits')
            logger.error('value error occurred while getting all labels')
        except Exception:
            smd = Smd_Response()
            logger.error('parent exception occurred while getting all labels')
        return smd


class UpdateAndDeleteLabel(GenericAPIView):
    serializer_class = LabelSerializers

    permission_classes = (IsAuthenticated,)

    def put(self, request, label_id, *args, **kwargs):
        """

        :param request: user request for put operation
        :param label_id: here we pass label_id  for specific update
        :return:this function used for update a label

        """
        try:
            user = request.user
            label = Label.objects.get(pk=int(label_id), user_id=user.id)
            if label:
                label.name = request.data['name']
                label.save()
                label_update_in_redis(user)
                smd = Smd_Response(True, 'label updated successfully', status_code=200)
                logger.info('label updated successfully')
            else:
                smd = Smd_Response(False, 'please enter valid label id or user id ')
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid label id or user id ')
            logger.error('label not exist for this label id error from Note.views')
        except ValueError:
            smd = Smd_Response(False, 'please enter label id in digits')
            logger.error('value error occurred in Note.views')
        except Exception:
            logger.error('parent exception occurred in Note.views.label_crud')
            smd = Smd_Response()
        return smd

    def delete(self, request, label_id, *args, **kwargs):
        """

        :param request: user request for delete label
        :param label_id:here we pass label id for specific delete
        :return:this function used for perform delete operation of label

        """
        try:
            Label.objects.get(pk=int(label_id)).delete()
            user = request.user
            label_update_in_redis(user)
            smd = Smd_Response(False, 'label deleted successfully', status_code=200)
            logger.info('label deleted successfully')
        except Label.DoesNotExist:
            logger.error('label not exist for this label id error from Note.views')
            smd = Smd_Response(False, 'please enter valid label_id ')
        except ValueError:
            logger.error('value error occurred in Note.views')
            smd = Smd_Response(False, 'please enter label id in digits ')
        except Exception:
            logger.error('parent exception occurred in Note.views.label_crud')
            smd = Smd_Response()
        return smd


class Reminders(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            print(request.user)
            data = Listing_Pages().reminder_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


class Trash_Notes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            print(request.user)
            data = Listing_Pages().trash_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


class Archive_Notes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            print(request.user)
            data = Listing_Pages().archive_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd
