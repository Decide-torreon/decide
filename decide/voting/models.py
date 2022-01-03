import urllib
from django.db import models
from django.contrib.postgres.fields import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.utils.translation import gettext_lazy as _

from base import mods
from base.models import Auth, Key


import zipfile

class Question(models.Model):
    desc = models.TextField()
    is_yes_no_question = models.BooleanField(default=False)
    

    def save(self):
        super().save()
        
        if self.is_yes_no_question:
            if self.options.all().count()>=1:
                self.options.all().delete()
    
            question_yes = QuestionOption(option = 'Yes', number = 0, question = self)
            question_yes.save()

            question_no = QuestionOption(option = 'No', number = 1, question = self)
            question_no.save()
        
        

    def __str__(self):
        return self.desc


class QuestionOption(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    number = models.PositiveIntegerField(blank=True, null=True)
    option = models.TextField()

    def save(self):
        if not self.number:
            self.number = self.question.options.count() + 2
        return super().save()

    def __str__(self):
        return '{} ({})'.format(self.option, self.number)


class Voting(models.Model):
    name = models.CharField(max_length=200)
    desc = models.TextField(blank=True, null=True)
    question = models.ForeignKey(Question, related_name='voting', null=True, on_delete=models.CASCADE)

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    pub_key = models.OneToOneField(Key, related_name='voting', blank=True, null=True, on_delete=models.SET_NULL)
    auths = models.ManyToManyField(Auth, related_name='votings')

    tally = JSONField(blank=True, null=True)
    postproc = JSONField(blank=True, null=True)

    TYPES = (
        ('Importante', 'Importante'),
        ('Informativa', 'Informativa'),
        ('Urgente', 'Urgente'),
        ('Prueba', 'Prueba'),
    )
    category = models.CharField(max_length=1000, choices=TYPES, blank=True)
    

    #url = models.CharField(max_length=40)
    url = models.CharField(max_length=40, help_text=u"http://localhost:8000/booth/",null=True)

    def clean_fields(self, exclude=None):
        super(Voting, self).clean_fields(exclude)

        url = urllib.parse.quote_plus(self.url.encode('utf-8'))

        if Voting.objects.filter(url=url).exists():
            raise ValidationError({'url': "The url already exists."})

    def save(self, *args, **kwargs):
        #self.url = urllib.parse.quote_plus(self.url.encode('utf-8'))
        try:
            Voting.objects.get(name=self.name)
        except:
            encode_url = urllib.parse.quote_plus(self.url.encode('utf-8'))
            self.url = encode_url
        print("self.url", self.url)
        super(Voting, self).save(*args, **kwargs)

    def create_pubkey(self):
        if self.pub_key or not self.auths.count():
            return

        auth = self.auths.first()
        data = {
            "voting": self.id,
            "auths": [ {"name": a.name, "url": a.url} for a in self.auths.all() ],
        }
        key = mods.post('mixnet', baseurl=auth.url, json=data)
        pk = Key(p=key["p"], g=key["g"], y=key["y"])
        pk.save()
        self.pub_key = pk
        self.save()

    def get_votes(self, token=''):
        # gettings votes from store
        votes = mods.get('store', params={'voting_id': self.id}, HTTP_AUTHORIZATION='Token ' + token)
        # anon votes
        return [[i['a'], i['b']] for i in votes]

    def tally_votes(self, token=''):
        '''
        The tally is a shuffle and then a decrypt
        '''

        votes = self.get_votes(token)

        auth = self.auths.first()
        shuffle_url = "/shuffle/{}/".format(self.id)
        decrypt_url = "/decrypt/{}/".format(self.id)
        auths = [{"name": a.name, "url": a.url} for a in self.auths.all()]

        # first, we do the shuffle
        data = { "msgs": votes }
        response = mods.post('mixnet', entry_point=shuffle_url, baseurl=auth.url, json=data,
                response=True)
        if response.status_code != 200:
            # TODO: manage error
            pass

        # then, we can decrypt that
        data = {"msgs": response.json()}
        response = mods.post('mixnet', entry_point=decrypt_url, baseurl=auth.url, json=data,
                response=True)

        if response.status_code != 200:
            # TODO: manage error
            pass

        self.tally = response.json()
        self.save()

        self.do_postproc()

    def do_postproc(self):
        tally = self.tally
        options = self.question.options.all()

        opts = []
        for opt in options:
            if isinstance(tally, list):
                votes = tally.count(opt.number)
            else:
                votes = 0
            opts.append({
                'option': opt.option,
                'number': opt.number,
                'votes': votes
            })

        data = { 'type': 'IDENTITY', 'options': opts }
        postp = mods.post('postproc', json=data)

        self.postproc = postp
        self.save()

        archivo = open("tallydeVoting"+str((self.id))+".txt","w")
        archivo.write("\n Hola Mundo\n")
        archivo.write(str((opts)))
        archivo.close()

        zip_file=zipfile.ZipFile("tally.zip", mode="w")
        zip_file.write("tallydeVoting"+str((self.id))+".txt")
        zip_file.close()
        return zip_file

    def __str__(self):
        return self.name 

class MultiVoting(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=60)
    desc = models.TextField()

    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.title

    def addMultiQuestion(self,multiQuestion):
        multiQuestion.multiVoting = self
        multiQuestion.save()
    
    def numberMultiQuestion(self):
        return MultiQuestion.objects.filter(multiVoting_id=self.id).count()

class MultiQuestion(models.Model):
    id = models.AutoField(primary_key=True)
    multiVoting = models.ForeignKey(MultiVoting,on_delete = models.CASCADE)
    question = models.CharField(max_length=50)
    
    def MultiVoting_Name(self):
        return self.multiVoting.title
    
    def __str__(self):
        return self.question

    def number_Options(self):
        return MultiOption.objects.filter(multiQuestion_id=self.id).count()

    def addMultiOption(self, multiOption):
        multiOption.multiQuestion = self
        multiOption.save()

    def countMultiOption(self):
        options = MultiOption.objects.filter(multiQuestion_id=self.id).values('option', 'numberVoted')
        res = {}
        for option in options:
            res[option['option']] = opcion['numberVoted']
        return res

    def voteMultiOption(self, selectedOptions):
        for option in selectedOptions:
            option.multiQuestion = self
            option.numberVoted = option.numberVoted + 1
            option.save()

class MultiOption(models.Model):
    id = models.AutoField(primary_key=True)
    multiQuestion = models.ForeignKey(MultiQuestion,on_delete = models.CASCADE)
    option= models.CharField(max_length=100)
    numberVoted = models.PositiveIntegerField(blank=True, null=True,default=0)

    def __str__(self):
        return self.option

    def MultiQuestion_Name(self):
        return self.multiQuestion.question

    def voteOption(self):
        self.numberVoted = self.numberVoted + 1
        self.save()
        
