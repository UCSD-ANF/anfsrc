#!/usr/bin/env python
"""Describe file"""

import django
from django.template import Template, Context
from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.template import Context


settings.configure()
django.setup()


settings.TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            # ... some options here ...
        },
    },
]


template = Template("""
{% autoescape off %}
ANF CONSTRUCTION REPORT RECEPTION REPORT

RECEIVED REPORT

From: {{ email.from_ }}
Date: {{ email.date }}
Subject: {{ email.subject }}


STATION

code: {{ sta }}
date: {{ date }}
gps: {{ lat }} N, {{ lon }} E
elev: {{ elev }}m


REPORT DISPOSITION

{{ disposition }}


ERRORS
{% for err in errors %}
{{ forloop.counter0 }}: {{ err|stringformat:"r" }}
{% endfor %}

DEBUGGING

Program: {{ argvzero }}
Hostname: {{ hostname }}
Database: {{ db }}
Platform: {{ platform }}
Python: {{ executable }}
Python Version: {{ pythonversion }}
{# Python Path: {{ pythonpath }} #}
{# {% debug %} #}
{% endautoescape %}
""".strip())


def render_template(**kwargs):
    c = Context(kwargs)
    return template.render(c)


def send_report(text_content):
    email = EmailMultiAlternatives('CONSTRUCTION REPORT', text_content)
    email.to = ['jeff@localhost']
    email.send()
