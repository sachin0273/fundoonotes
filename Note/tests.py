import json
import pdb

from django.test import TestCase, Client

# Create your tests here.
from django.urls import reverse
import requests
from users import urls
from utils import load
from django.conf import settings

BASE_URL = settings.BASE_URL


def test_login_user():
    global header
    url = settings.BASE_URL + reverse('users')
    data = load('Note/note_test.json')
    user = data['user_login'][0]
    response = requests.post(url, user)
    token = json.loads(response.content)
    header = {'HTTP_AUTHORIZATION': 'Bearer ' + token['data']}
    assert response.status_code == 200


class NoteAppTest(TestCase):
    fixtures = ['fixtures/django_db']

    def test_wrong_collaborator_and_label(self):
        data = load('Note/note_test.json')
        notes = data['note_create'][0]
        url = BASE_URL + reverse('notes')
        c = Client()
        response = c.post(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)

    def test_wrong_collaborator_and_label_2(self):
        data = load('Note/note_test.json')
        notes = data['note_create'][1]
        url = BASE_URL + reverse('notes')
        c = Client()
        response = c.post(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)

    def test_valid_collaborator_and_label(self):
        data = load('Note/note_test.json')
        notes = data['note_create'][2]
        url = BASE_URL + reverse('notes')
        c = Client()
        response = c.post(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_update_note_1(self):
        data = load('Note/note_test.json')
        notes = data['note_update'][0]
        url = BASE_URL + reverse('note', args=['41'])
        c = Client()
        response = c.put(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_update_note_2(self):
        data = load('Note/note_test.json')
        notes = data['note_update'][1]
        url = BASE_URL + reverse('note', args=['41'])
        c = Client()
        response = c.put(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_update_note_3(self):
        data = load('Note/note_test.json')
        notes = data['note_update'][2]
        url = BASE_URL + reverse('note', args=['41'])
        c = Client()
        response = c.put(url, notes, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_note_delete_valid(self):
        data = load('Note/note_test.json')
        id = data['note_crud'][0]['note_id']
        url = BASE_URL + reverse('note', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_note_delete_blank_input(self):
        data = load('Note/note_test.json')
        id = data['note_crud'][1]['note_id']
        url = BASE_URL + reverse('note', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_note_delete_invalid_input(self):
        data = load('Note/note_test.json')
        id = data['note_crud'][2]['note_id']
        url = BASE_URL + reverse('note', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_note_delete_string_input(self):
        data = load('Note/note_test.json')
        id = data['note_crud'][3]['note_id']
        url = BASE_URL + reverse('note', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_get_all_note_valid_user_id(self):
        data = load('Note/note_test.json')
        id = data['get_all_note'][0]['user_id']
        url = BASE_URL + reverse('notes')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_all_note_valid_user_id_2(self):
        data = load('Note/note_test.json')
        id = data['get_all_note'][0]['user_id']
        url = BASE_URL + reverse('notes')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_create_label_valid_input(self):
        data = load('Note/note_test.json')
        label = data['label_create'][0]
        url = BASE_URL + reverse('labels')
        c = Client()
        response = c.post(url, label, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_create_label_invalid_input(self):
        data = load('Note/note_test.json')
        label = data['label_create'][1]
        url = BASE_URL + reverse('labels')
        c = Client()
        response = c.post(url, label, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)

    def test_put_label_valid_input(self):
        data = load('Note/note_test.json')
        label = data['put_label'][0]
        url = BASE_URL + reverse('label', args=['7'])
        c = Client()
        response = c.put(url, label, content_type='application/json', **header)
        self.assertEqual(response.status_code, 200)

    def test_put_label_valid_input_2(self):
        data = load('Note/note_test.json')
        label = data['put_label'][0]
        url = BASE_URL + reverse('label', args=['dfffdfg'])
        c = Client()
        response = c.put(url, label, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)

    def test_put_label_valid_input_3(self):
        data = load('Note/note_test.json')
        label = data['put_label'][0]
        url = BASE_URL + reverse('label', args=['89'])
        c = Client()
        response = c.put(url, label, content_type='application/json', **header)
        self.assertEqual(response.status_code, 400)

    def test_label_delete_valid(self):
        data = load('Note/note_test.json')
        id = data['delete_label'][0]['label_id']
        url = BASE_URL + reverse('label', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_label_delete_blank_input(self):
        data = load('Note/note_test.json')
        id = data['delete_label'][1]['label_id']
        url = BASE_URL + reverse('label', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_label_delete_invalid_input(self):
        data = load('Note/note_test.json')
        id = data['delete_label'][2]['label_id']
        url = BASE_URL + reverse('label', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_label_delete_string_input(self):
        data = load('Note/note_test.json')
        id = data['delete_label'][3]['label_id']
        url = BASE_URL + reverse('label', args=[id])
        c = Client()
        response = c.delete(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_get_all_label_valid_user_id(self):
        data = load('Note/note_test.json')
        id = data['get_all_label'][0]['user_id']
        url = BASE_URL + reverse('labels')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_all_label_valid_2(self):
        data = load('Note/note_test.json')
        id = data['get_all_label'][0]['user_id']
        url = BASE_URL + reverse('labels')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_reminder_notes(self):
        url = BASE_URL + reverse('reminder')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_reminder_notes_2(self):
        url = BASE_URL + reverse('reminder')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_trash_notes(self):
        url = BASE_URL + reverse('trash')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_trash_notes_2(self):
        url = BASE_URL + reverse('trash')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_archive_notes(self):
        url = BASE_URL + reverse('archive')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_get_archive_notes_2(self):
        url = BASE_URL + reverse('archive')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_pagination(self):
        url = BASE_URL + reverse('pagination')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_elastic_search_1(self):
        url = BASE_URL + reverse('search', args=['78'])
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_elastic_search_2(self):
        url = BASE_URL + reverse('search', args=['90'])
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 400)

    def test_pinned_note(self):
        url = BASE_URL + reverse('pin')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)

    def test_pinned_note_2(self):
        url = BASE_URL + reverse('pin')
        c = Client()
        response = c.get(url, **header)
        self.assertEqual(response.status_code, 200)
