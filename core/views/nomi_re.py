from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.shortcuts import render,HttpResponse
from django.views.generic.edit import CreateView, UpdateView, DeleteView

import csv, json
from datetime import date,datetime
from itertools import chain
from operator import attrgetter


from forms.models import Questionnaire
from forms.views import replicate
from core.models import *
from core.forms import *
from .nomi_cr import get_access_and_post_for_result, get_access_and_post

## ------------------------------------------------------------------------------------------------------------------ ##
#########################################   REOPEN NOMINATION MONITOR VIEWS   ##########################################
## ------------------------------------------------------------------------------------------------------------------ ##


@login_required
def reopen_nomi(request, nomi_pk):
    access , view_post = get_access_and_post(request,nomi_pk)
    nomi = Nomination.objects.get(pk=nomi_pk)
    if access:
        re_nomi = ReopenNomination.objects.create(nomi=nomi)
        re_nomi.approvals.add(view_post)
        if view_post.elder_brother:
            re_nomi.approvals.add(view_post.elder_brother)
        re_nomi.nomi.status = 'Interview period and Reopening initiated'
        re_nomi.nomi.save()
        return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))
    else:
        return render(request, 'no_access.html')


# ****** in use...
def get_access_and_post_for_renomi(request,re_nomi_pk):
    re_nomi = ReopenNomination.objects.get(pk=re_nomi_pk)
    access = False
    view_post = None
    for post in re_nomi.approvals.all():
        if request.user in post.post_holders.all():
            access = True
            view_post = post
            break
    return access,view_post


@login_required
def re_nomi_approval(request, re_nomi_pk):
    re_nomi = ReopenNomination.objects.get(pk=re_nomi_pk)
    access , view_post = get_access_and_post_for_renomi(request,re_nomi_pk)

    if access:
        if view_post.perms == "can ratify the post" or view_post.perms =="can approve post and send nominations to users":
            re_nomi.re_open_to_users()
            nomi = re_nomi.nomi
            re_nomi.delete()
            return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi.pk}))
        else:
            to_add = view_post.elder_brother
            re_nomi.approvals.add(to_add)
            return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': re_nomi.nomi.pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def re_nomi_reject(request, re_nomi_pk):
    re_nomi = ReopenNomination.objects.get(pk=re_nomi_pk)
    access , view_post = get_access_and_post_for_renomi(request,re_nomi_pk)
    if access:
        nomi = re_nomi.nomi
        nomi.status = 'Interview period'
        nomi.save()
        re_nomi.delete()
        return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi.pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def final_re_nomi_approval(request, re_nomi_pk):
    re_nomi = ReopenNomination.objects.get(pk=re_nomi_pk)
    access , view_post = get_access_and_post_for_renomi(request,re_nomi_pk)

    if access:
        re_nomi.re_open_to_users()
        nomi=re_nomi.nomi
        re_nomi.delete()
        return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi.pk}))
    else:
        return render(request, 'no_access.html')
