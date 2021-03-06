import json
import pdb

from elasticsearch_dsl import MultiSearch, Search
from django.shortcuts import render
from rest_framework.views import APIView

from .documents import NoteDocument
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
from Note.serializers import NoteSerializers, LabelSerializers, NotesSerializer, NoteSerializerPut
from utils import Smd_Response
from users.decoraters import login_required
from django.contrib.auth.models import User
from .service.note import NoteService, update_redis, label_update_in_redis
from django.contrib.auth.models import User
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

logger = logging.getLogger(__name__)


class NoteView(GenericAPIView):
    serializer_class = NoteSerializers

    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        """

        :param request:user request for create a note
        :return:this function is used for create new note and save

        """

        try:
            request_data = request.data
            if "collaborator" in request_data:
                collaborators = request_data['collaborator']
                result = NoteService().add_collaborator(collaborators)
                if not result['success']:
                    return HttpResponse(json.dumps(result))
                request_data['collaborator'] = result['data']
            if "label" in request_data:
                labels = request_data['label']
                label_result = NoteService().add_label(labels)
                if not label_result['success']:
                    return HttpResponse(json.dumps(label_result))
                request_data['label'] = label_result['data']
            serializer = NoteSerializers(data=request_data, partial=True)
            if serializer.is_valid():
                serializer.save(user=request.user)
                user = request.user
                update_redis(user)
                smd = Smd_Response(True, 'successfully note updated', data=[serializer.data], status_code=200)
                logger.info('successfully note updated')
            else:
                smd = Smd_Response(False, serializer.errors, [])
        except Exception as e:
            smd = Smd_Response()
            logger.error('something was wrong ' + str(e))
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
                serializer = NotesSerializer(notes, many=True)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('successfully get notes from redis')
                return smd
            all_notes = Note.objects.filter(user_id=int(user.id), is_trash=False, is_archive=False)
            if all_notes:
                serializer = NotesSerializer(all_notes, many=True)
                note = pickle.dumps(all_notes)
                redis.Set(user.username, note)
                smd = Smd_Response(True, 'successfully', data=serializer.data, status_code=200)
                logger.info('successfully get notes from database')
            else:
                smd = Smd_Response(False, 'please enter valid user id')
        except Note.DoesNotExist:
            smd = Smd_Response(False, 'please enter valid user for get a note')
            logger.error('note not exist for this note id ')
        except ValueError:
            smd = Smd_Response(False, 'please enter user_id in digits')
        except Exception as e:
            logger.error('exception occurred while getting all notes' + str(e))
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


class NoteDetailsView(GenericAPIView):
    serializer_class = NoteSerializerPut

    permission_classes = (IsAuthenticated,)

    # parser_classes = (MultiPartParser, FormParser,)

    def put(self, request, note_id, *args, **kwargs):
        """
        :param request: user request for put operation
        :param note_id: here we pass note id for specific update
        :return:this function used for update a note
        """

        try:
            # request_data = json.loads(request.body)
            request_data = request.data

            if "collaborator" in request_data:
                collaborators = request_data['collaborator']
                result = NoteService().add_collaborator(collaborators)
                if not result['success']:
                    return HttpResponse(json.dumps(result))
                request_data['collaborator'] = result['data']
            if "label" in request_data:
                labels = request_data['label']
                label_result = NoteService().add_label(labels)
                if not label_result['success']:
                    return HttpResponse(json.dumps(label_result))
                request_data['label'] = label_result['data']
            update_note = Note.objects.get(pk=int(note_id))
            serializer = NoteSerializerPut(instance=update_note, data=request_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                user = request.user
                update_redis(user)
                smd = Smd_Response(True, 'successfully note updated', data=[serializer.data], status_code=200)
                logger.info('successfully note updated')
            else:
                smd = Smd_Response(False, serializer.errors)
        except Exception as e:
            smd = Smd_Response()
            logger.error('something was wrong ' + str(e))
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
        except Note.DoesNotExist as e:
            logger.error('note does not exist for this note id error from Note.views' + str(e))
            smd = Smd_Response(False, 'please enter valid note_id')
        except ValueError as e:
            smd = Smd_Response(False, 'please enter note_id in digits' + str(e))
        except Exception as e:
            logger.error('parent exception occurred ' + str(e))
            smd = Smd_Response()
        return smd


class LabelView(GenericAPIView):
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
        except Exception as e:
            smd = Smd_Response()
            logger.error('something was wrong ' + str(e))
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
                smd = Smd_Response(False, 'for this user label not exist')
        except Label.DoesNotExist:
            smd = Smd_Response(False, 'for this user id label not available please enter valid user_id')
            logger.error('for this user id label not exist error from Note.views.get_label')
        except ValueError as e:
            smd = Smd_Response(False, 'please enter user id in digits')
            logger.error('value error occurred while getting all labels' + str(e))
        except Exception as e:
            smd = Smd_Response()
            logger.error('parent exception occurred while getting all labels' + str(e))
        return smd


class LabelDetailsView(GenericAPIView):
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
        except ValueError as e:
            smd = Smd_Response(False, 'please enter label id in digits')
            logger.error('value error occurred ' + str(e))
        except Exception as e:
            logger.error('parent exception occurred' + str(e))
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
        except ValueError as e:
            logger.error('value error occurred' + str(e))
            smd = Smd_Response(False, 'please enter label id in digits ')
        except Exception as e:
            logger.error('parent exception occurred' + str(e))
            smd = Smd_Response()
        return smd


class Reminders(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """

        :param request: user request for get all reminder notes
        :return: this function is used for return all reminder nits fired or upcoming

        """
        try:
            user = request.user
            print(request.user)
            data = NoteService().reminder_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


class TrashNotes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """

        :param request:user request for get all trash notes
        :return:this function return all trashed notes

        """
        try:
            user = request.user
            print(request.user)
            data = NoteService().trash_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


class ArchiveNotes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """

        :param request: user request for get archive notes
        :return:this function is used for return all archive notes

        """
        try:
            user = request.user
            print(request.user)
            data = NoteService().archive_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


class PinnedNotes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        """

        :param request: user request for get archive notes
        :return:this function is used for return all archive notes

        """
        try:
            user = request.user
            data = NoteService().pin_notes(user)
            if data['success']:
                return HttpResponse(json.dumps(data, indent=1), status=200)
            else:
                return HttpResponse(json.dumps(data), status=400)
        except Exception:
            smd = Smd_Response()
            return smd


def pagination(request):
    """

    :param request:user request for get pages
    :return:this function used for pagination means gives data after request of page

    """
    try:
        note_list = Note.objects.all()
        paginator = Paginator(note_list, 10)
        page = request.GET.get('page', 1)
        notes = paginator.page(page)
    except PageNotAnInteger:
        notes = paginator.page(1)
    except EmptyPage:
        notes = paginator.page(paginator.num_pages)
    except Exception:
        smd = Smd_Response()
        return smd
    return render(request, 'users/pagination.html', {'notes': notes})


class SearchNotes(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, search_note):
        """

        :param request: user request for search note
        :param search_note: here we passing parameter for search note
        :return: this function return searched notes using elasticsearch search engine

        """
        try:
            # pdb.set_trace()
            user = request.user
            notes = NoteDocument.search().query({
                "bool": {"must": {

                    "multi_match": {
                        "query": search_note,
                        "fields": ['label.name', 'title', 'note', 'reminder', 'color']
                    }
                },

                    "filter": {
                        "term": {
                            'user_id': user.id
                        }

                    }
                }
            })
            total_count = notes.count()
            print(total_count)
            if total_count != 0:
                searched_notes = notes.to_queryset()
                print(searched_notes)
                serializer = NotesSerializer(searched_notes, many=True)
                print(serializer.data)
                # print(value_count)
                # # # print(json.dumps(posts))
                # result = notes[0:total_count].execute()
                # all_notes = result.to_dict()
                smd = Smd_Response(True, 'successfully', serializer.data, 200)
                logger.info('successfully notes searched and returned')
            else:
                logger.warning('for this search note does not exist')
                smd = Smd_Response(message='for this search note does not exist')
        except Exception as e:
            logger.error('while searching a notes exception accrued' + str(e))
            smd = Smd_Response()
        return smd
