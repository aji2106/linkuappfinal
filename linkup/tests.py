from django.test import TestCase
from django.test import Client
from django.contrib.auth import login
from linkup.models import Profile,Event,Poll
from django.contrib.auth.models import User


class CsrTest(TestCase):

    # Tests if csrfmiddlewaretoken is in the login page
    def login(self):
        client = Client()
        response1 = client.get('/login/')
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1,'csrfmiddlewaretoken')

# Tests user login with sample username and password data
class linkup(TestCase):
    def checkuserlogin(self):
        client = Client()
        u = 'testuser'
        p = 'password'
        e = 'testemail@gmail.com'
        User.objects.create(username=u, password=p, email=e)
        query = {
        'username' : u,
        'password' : p,
        'email'    : e,

        }
        response2 = client.post('/login/',query)
        self.assertEqual(response2.status_code, 302)
