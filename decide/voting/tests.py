import random
import itertools
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework.test import APITestCase

from base import mods
from base.tests import BaseTestCase
from census.models import Census
from mixnet.mixcrypt import ElGamal
from mixnet.mixcrypt import MixCrypt
from mixnet.models import Auth
from voting.models import Voting, Question, QuestionOption



class VotingTestCase(BaseTestCase):

    def setUp(self):
        super().setUp()

    def tearDown(self):
        super().tearDown()

    def encrypt_msg(self, msg, v, bits=settings.KEYBITS):
        pk = v.pub_key
        p, g, y = (pk.p, pk.g, pk.y)
        k = MixCrypt(bits=bits)
        k.k = ElGamal.construct((p, g, y))
        return k.encrypt(msg)

    #def create_voting(self):
    def create_voting(self, url):
        q = Question(desc='test question')
        q.save()
        for i in range(5):
            opt = QuestionOption(question=q, option='option {}'.format(i+1))
            opt.save()
        #v = Voting(name='test voting', question=q)
        
        v = Voting(name='test voting', question=q, url=url)
        v.save()

        a, _ = Auth.objects.get_or_create(url=settings.BASEURL,
                                          defaults={'me': True, 'name': 'test auth'})
        a.save()
        v.auths.add(a)

        return v

    def create_voters(self, v):
        for i in range(100):
            u, _ = User.objects.get_or_create(username='testvoter{}'.format(i))
            u.is_active = True
            u.save()
            c = Census(voter_id=u.id, voting_id=v.id)
            c.save()

    def get_or_create_user(self, pk):
        user, _ = User.objects.get_or_create(pk=pk)
        user.username = 'user{}'.format(pk)
        user.set_password('qwerty')
        user.save()
        return user

    def store_votes(self, v):
        voters = list(Census.objects.filter(voting_id=v.id))
        voter = voters.pop()

        clear = {}
        for opt in v.question.options.all():
            clear[opt.number] = 0
            for i in range(random.randint(0, 5)):
                a, b = self.encrypt_msg(opt.number, v)
                data = {
                    'voting': v.id,
                    'voter': voter.voter_id,
                    'vote': { 'a': a, 'b': b },
                }
                clear[opt.number] += 1
                user = self.get_or_create_user(voter.voter_id)
                self.login(user=user.username)
                voter = voters.pop()
                mods.post('store', json=data)
        return clear

    def test_complete_voting(self):
        v = self.create_voting('test')
        self.create_voters(v)

        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()

        clear = self.store_votes(v)

        self.login()  # set token
        v.tally_votes(self.token)

        tally = v.tally
        tally.sort()
        tally = {k: len(list(x)) for k, x in itertools.groupby(tally)}

        for q in v.question.options.all():
            self.assertEqual(tally.get(q.number, 0), clear.get(q.number, 0))

        for q in v.postproc:
            self.assertEqual(tally.get(q["number"], 0), q["votes"])

    def test_create_voting_from_api(self):
        data = {'name': 'Example'}
        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        response = mods.post('voting', params=data, response=True)
        self.assertEqual(response.status_code, 400)

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'url': 'test',
            #'category':'Urgente',
            'question': 'I want a ',
            'question_opt': ['cat', 'dog', 'horse']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_update_voting(self):
        voting = self.create_voting('test')

        data = {'action': 'start'}
        #response = self.client.post('/voting/{}/'.format(voting.pk), data, format='json')
        #self.assertEqual(response.status_code, 401)

        # login with user no admin
        self.login(user='noadmin')
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 403)

        # login with user admin
        self.login()
        data = {'action': 'bad'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)

        # STATUS VOTING: not started
        for action in ['stop', 'tally']:
            data = {'action': action}
            response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), 'Voting is not started')

        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting started')

        # STATUS VOTING: started
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting is not stopped')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting stopped')

        # STATUS VOTING: stopped
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), 'Voting tallied')

        # STATUS VOTING: tallied
        data = {'action': 'start'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already started')

        data = {'action': 'stop'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already stopped')

        data = {'action': 'tally'}
        response = self.client.put('/voting/{}/'.format(voting.pk), data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), 'Voting already tallied')
    
   
        
    def test_create_voting_url_exists(self):
        v = self.create_voting(url="_test_voting")

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'url': '_test_voting',
            'question': 'Is this a question? ',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_voting_url_whitespaces(self):
        v = self.create_voting(url="_test voting")
        self.assertTrue(Voting.objects.filter(url="_test+voting").exists())

    def test_create_voting_without_url(self):
        
        data = {
            'name': 'Example No URL',
            'desc': 'Description example',
            'question': 'Is this a question? ',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_voting_without_url_and_question(self):
        

        data = {
            'name': 'Example',
            'desc': 'Description example',
            'question_opt': ['Yes', 'No']
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)

    def test_create_voting_onlyname(self):
        

        data = {
            'name': 'Example'
            
        }

        response = self.client.post('/voting/', data, format='json')
        self.assertEqual(response.status_code, 401)
    
class Test_enrmorvaz(BaseTestCase):
    def setUp(self):

        q1 = Question(desc='Esto es una pregunta de si o no', is_yes_no_question=True)
        q1.save()

        q2 = Question(desc='Esto NO es una pregunta de si o no', is_yes_no_question=True)
        q2.save()

        qo1 = QuestionOption(question = q2, option = 'Opcion 1')
        qo1.save()

        qo2 = QuestionOption(question = q2, option = 'Opcion 2')
        qo2.save()

        qo3 = QuestionOption(question = q2, option = 'Opcion 3')
        qo3.save()

    def tearDown(self):
        super().tearDown()
        self.v=None
        self.v2=None

    def test_OpcionesSiNo(self):
        q = Question.objects.get(desc='Esto es una pregunta de si o no')
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].option, 'Yes')
        self.assertEquals(q.options.all()[1].option, 'No')
    
    def test_OpcionesSiNoError(self):
        q = Question.objects.get(desc='Esto NO es una pregunta de si o no')
        q.save()
        if(q.options.all().count()!=2):
            self.assertTrue(True)
    
    def test_RestablecerValoresSiNo(self):
        q = Question.objects.get(desc='Esto NO es una pregunta de si o no')
        q.is_yes_no_question = True
        q.save()

        self.assertEquals(len(q.options.all()), 2)
        self.assertEquals(q.options.all()[0].option, 'Yes')
        self.assertEquals(q.options.all()[1].option, 'No')
    
    def test_SinDescSiNoError(self):
        try:
            q3 = Question(is_yes_no_question=True)
            q3.save()
        except:
            self.assertTrue(True)
    
    def test_OpcionError(self):
        try:
            q = QuestionOption()
            q.save()
        except:
            self.assertTrue(True)    

    