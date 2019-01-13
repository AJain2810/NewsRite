from django.shortcuts import render
import urllib.request
from bs4 import BeautifulSoup
from django.http import HttpResponse
from django.template import loader
from .models import Website
from google.cloud import language_v1, language
from google.cloud.language import enums
from google.cloud.language import types

from googleapiclient.discovery import build
import six

import os
import re




os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/mnt/c/Users/abhin/Dropbox/Projects/NewsRite/Django/Django/apikey.json"


def sample_analyze_sentiment(content):
    client = language_v1.LanguageServiceClient()
    if isinstance(content, six.binary_type):
        content = content.decode('utf-8')
    type_ = enums.Document.Type.PLAIN_TEXT
    document = {'type': type_, 'content': content}
    response = client.analyze_sentiment(document)
    sentiment = response.document_sentiment
    # print('Score: {}'.format(sentiment.score))
    # print('Magnitude: {}'.format(sentiment.magnitude))
    return sentiment


def entities_text(text):
    """Detects entities in the text."""
    client = language.LanguageServiceClient()
    if isinstance(text, six.binary_type):
        text = text.decode('utf-8')
    # Instantiates a plain text document.
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)
    # Detects entities in the document. You can also analyze HTML with:
    #   document.type == enums.Document.Type.HTML
    entities = client.analyze_entities(document).entities
    # entity types from enums.Entity.Type
    entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
                   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')
    """for entity in entities:
        print('=' * 20)
        print(u'{:<16}: {}'.format('name', entity.name))
        print(u'{:<16}: {}'.format('type', entity_type[entity.type]))
        print(u'{:<16}: {}'.format('metadata', entity.metadata))
        print(u'{:<16}: {}'.format('salience', entity.salience))
        print(u'{:<16}: {}'.format('wikipedia_url',
                                   entity.metadata.get('wikipedia_url', '-')))"""
    return entities


# Create your views here.

def index(request):
    allWebsites=Website.objects.all()
    template = loader.get_template('newsrite/index.html')
    context = {
        'allWebsites' : allWebsites,
    }

    return HttpResponse(template.render(context, request))

def checkForURL(string):
    # findall() has been used
    # with valid conditions for urls in string
    url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]| [! * \(\),] | (?: %[0-9a-fA-F][0-9a-fA-F]))+', string)
    return len(url)>0


def search(request):
    if request.method == "GET":
        search_query = request.GET.get("search", None)
        status=checkForURL(search_query)
        name = ''
        if status == True:
            page = urllib.request.urlopen(search_query)
            soup = BeautifulSoup(page, 'html.parser')
            name_box = soup.find('h1')
            name = name_box.text.strip()
        else:
            name = search_query
        sentiment = sample_analyze_sentiment(name) #nlp called
        entities = entities_text(name)

        query =""

        for entity in entities:
            query+=entity.name
            query+=" "

        service = build("customsearch", "v1",
                        developerKey="AIzaSyCWQRtktQxa8FcZxPlutu2bdijisW2B19s")

        res = service.cse().list(
            q=query,
            cx='001322294919670783930:2czfzokqekk',
        ).execute()

        dict={}
        result = res["items"]

        score=0

        relevency=[]

        count2=0

        for entity in result:
            count1=0
            count2=0
            keywords = entity["title"]
            for ent in name.split():
                count2+=1
                for key in keywords.split():
                    if key.lower()==ent.lower():
                        count1+=1

            relevency.append(count1/count2)

        score = max(relevency[0:5])
        score = score*10
        if score>10:
            score=9.5

        """if len(res)>5:
            score = 9
        elif len(res)>4:
            score =7.5
        elif len(res)>3:
            score = 5
        else:
            score =2.5"""

        counter=0
        for entity in result:
            if counter==5:
                break
            dict[entity["title"]+"(Relevency:"+str(relevency[counter])+")"] = entity["link"]
            counter+=1


        template = loader.get_template('newsrite/detailpage.htm')

        context = {
            'URL' :  search_query,
            'sentiment': sentiment,
            'entities' : entities,
            'dict' : dict,
            'score' : score,
            'relevency' : relevency
        }

        return HttpResponse(template.render(context, request))