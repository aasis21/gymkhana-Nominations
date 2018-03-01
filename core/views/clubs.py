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

## ------------------------------------------------------------------------------------------------------------------ ##
#########################################    CLUB RELATED VIEWS   ######################################################
## ------------------------------------------------------------------------------------------------------------------ ##

# the viewer_post which have access add its parent for approval of club
# is_safe
@login_required
def club_approval(request, club_pk):
    club_create = ClubCreate.objects.get(pk=club_pk)
    access = False
    if request.user in club_create.take_approval.post_holders.all():
        access = True
        view = club_create.take_approval


    if access:
        if club_create.take_approval.perms == "can ratify the post":
            Club.objects.create(club_name = club_create.club_name,club_parent = club_create.club_parent)
            club_create.delete()
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': view.pk}))
        else:
            to_add = club_create.take_approval.parent
            club_create.take_approval = to_add
            club_create.save()
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': view.pk}))
    else:
        return render(request, 'no_access.html')

# the viewer removes himself from approvals ,thus delete the post down...
# is_safe
@login_required
def club_reject(request, club_pk):
    club_reject = ClubCreate.objects.get(pk=club_pk)

    access = False
    if request.user in club_reject.take_approval.post_holders.all():
        access = True
        view = club_reject.take_approval

    if access:
        club_reject.delete()

    return HttpResponseRedirect(reverse('post_view', kwargs={'pk': view.pk}))
