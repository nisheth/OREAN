"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

#from django.test import TestCase
#
#
#class SimpleTest(TestCase):
#    def test_basic_addition(self):
#        """
#        Tests that 1 + 1 always equals 2.
#        """
#        self.assertEqual(1 + 1, 2)

from django.test import TestCase
from django.test.client import Client
from api.models import *
import time

class TestAPI(TestCase):
    def setUp(self):
        self.client = Client()
        self.username = 'test'
        self.email = 'test@localhost'
        self.password = 'test'        
        self.test_user = User.objects.create_user(self.username, self.email, self.password)
        login = self.client.login(username=self.username, password=self.password)
        self.assertEqual(login, True)

    def test_listproject(self):
        print "Starting request..."
        start = time.time()
        response = self.client.get('/api/ListProjects/')
        end = time.time()
        print "Request Complete, took", end-start
        self.assertEqual(response.status_code, 200)

    def teardown(self):
        self.test_user.delete()

