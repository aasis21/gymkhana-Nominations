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
# from gymkhanaNominations import DOMAIN_NAME
from core.models import *
from core.forms import *

DOMAIN_NAME = 'sdhjh'
## ------------------------------------------------------------------------------------------------------------------ ##
#########################################    NOMINATION RELATED VIEWS   ################################################
## ------------------------------------------------------------------------------------------------------------------ ##

# only post parent should create nomi...
# safe
@login_required
def nomination_create(request, pk):
    post = Post.objects.get(pk=pk)
    if request.user in post.parent.post_holders.all():
        if request.method == 'POST':
            title_form = NominationForm(request.POST)
            if title_form.is_valid():
                post = Post.objects.get(pk=pk)

                questionnaire = Questionnaire.objects.create(name=title_form.cleaned_data['title'])

                nomination = Nomination.objects.create(name=title_form.cleaned_data['title'],
                                                   description=title_form.cleaned_data['description'],
                                                   deadline=title_form.cleaned_data['deadline'],
                                                   nomi_session=title_form.cleaned_data['nomi_session'],
                                                   nomi_form=questionnaire, nomi_post=post,
                                                   )

                pk = questionnaire.pk
                return HttpResponseRedirect(reverse('forms:creator_form', kwargs={'pk': pk}))

        else:
            title_form = NominationForm()

        return render(request, 'nomi/nomination_form.html', context={'form': title_form, 'post': post})

    else:
        return render(request, 'no_access.html')




class NominationUpdate(UpdateView):
    model = Nomination
    fields = ['name', 'description']
    success_url = reverse_lazy('index')


class NominationDelete(DeleteView):
    model = Nomination
    success_url = reverse_lazy('index')


def nomi_replicate(request,nomi_pk):
    nomi_to_replicate = Nomination.objects.get(pk = nomi_pk)
    post = nomi_to_replicate.nomi_post
    if request.user in post.parent.post_holders.all():
        if request.method == 'POST':
            title_form = NominationReplicationForm(request.POST)
            if title_form.is_valid():
                questionnaire = replicate(nomi_to_replicate.nomi_form.pk)
                questionnaire.name = title_form.cleaned_data['title']
                questionnaire.save()

                nomination = Nomination.objects.create(name=title_form.cleaned_data['title'],
                                                       description=nomi_to_replicate.description,
                                                       deadline=title_form.cleaned_data['deadline'],
                                                       nomi_session=title_form.cleaned_data['nomi_session'],
                                                       nomi_form=questionnaire, nomi_post=post,
                                                       )

                pk = questionnaire.pk
                return HttpResponseRedirect(reverse('forms:creator_form', kwargs={'pk': questionnaire.pk}))

        else:
            title_form = NominationReplicationForm()

            return render(request, 'nomi/nomination_form.html', context={'form': title_form, 'post': post})

    else:
        return render(request, 'no_access.html')


# ****** in use...
def get_access_and_post(request,nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access = False
    view_post = None
    for post in nomi.nomi_approvals.all():
        if request.user in post.post_holders.all():
            access = True
            view_post = post
            break
    return access,view_post

def get_access_and_post_for_result(request, nomi_pk):
    nomi =Nomination.objects.get(pk=nomi_pk)
    access = False
    view_post = None
    for post in nomi.result_approvals.all():
        if request.user in post.post_holders.all():
            access = True
            view_post = post
            break
    return access, view_post


@login_required
def nomi_detail(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    parents = nomi.nomi_post.parent.post_holders.all()
    questionnaire = nomi.nomi_form
    form = questionnaire.get_form(request.POST or None)

    panelform = UserId(request.POST or None)

    access, view_post = get_access_and_post(request, nomi_pk)
    if not access:
        access, view_post = get_access_and_post_for_result(request, nomi_pk)

    status = [None]*7
    renomi_edit = 0
    p_in_rn = 0
    if nomi.status == 'Nomination created':
        status[0] = True
    elif nomi.status == 'Nomination out':
        status[1] = True
    elif nomi.status == 'Interview period':
        status[2] = True
    elif nomi.status == 'Sent for ratification':
        status[3] = True
    elif nomi.status == 'Interview period and Reopening initiated':
        status[4] = True
        if view_post in nomi.reopennomination.approvals.all():
            renomi_edit = 1
            if view_post.parent in nomi.reopennomination.approvals.all():
                p_in_rn = 1

    elif nomi.status == 'Interview period and Nomination reopened':
        status[5] = True
    else:
        status[6] = True


    if access:
        if view_post.perms == 'can approve post and send nominations to users' or view_post.perms == 'can ratify the post':
            power_to_send = 1
        else:
            power_to_send = 0
        if view_post.elder_brother in nomi.nomi_approvals.all():
            sent_to_parent = 1
        else:
            sent_to_parent = 0




        if panelform.is_valid():
            try:
                profile = UserProfile.objects.get(roll_no=panelform.cleaned_data["user_roll"])
                user = profile.user
                nomi.interview_panel.add(user)
                return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))
            except ObjectDoesNotExist:
                return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))

        panelists = nomi.interview_panel.all().distinct()
        panelists_exclude_parent = []

        for panelist in panelists:
            if panelist not in parents:
                panelists_exclude_parent.append(panelist)

        return render(request, 'nomi_detail_admin.html', context={'nomi': nomi, 'form': form, 'panelform': panelform,
                                                                  'sent_to_parent': sent_to_parent, 'status': status,
                                                                  'power_to_send': power_to_send, 'parents': parents,
                                                                  'panelists': panelists_exclude_parent,'renomi':renomi_edit,
                                                                  'p_in_rn':p_in_rn})


    elif request.user in nomi.interview_panel.all():
        return render(request, 'nomi_detail_user.html', context={'nomi': nomi})


    else:
        if status[1] or status[5]:
            return render(request, 'nomi_detail_user.html', context={'nomi': nomi})
        else:
            return render(request, 'no_access.html')

@login_required
def see_nomi_form(request, pk):
    nomi = Nomination.objects.get(pk=pk)
    if nomi.nomi_form and nomi.nomi_form.question_set.all():
        questionnaire = nomi.nomi_form
        form = questionnaire.get_form
        return render(request, 'see_nomi_form.html', context={'form': form, 'nomi':nomi })
    else:
        info = "There is not any form for this nomi"

        return render(request, 'nomi_done.html', context={'info': info})


@login_required
def remove_panelist(request, nomi_pk, user_pk):
    nomination = Nomination.objects.get(pk=nomi_pk)
    panelist = User.objects.get(pk=user_pk)

    panel = nomination.interview_panel
    panel.remove(panelist)

    return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))


@login_required
def nomi_approval(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)

    access, view_post = get_access_and_post(request, nomi_pk)

    if access:
        if view_post.elder_brother:
            to_add = view_post.elder_brother
            nomi.nomi_approvals.add(to_add)
            nomi.tags.add(view_post.parent.club)
            nomi.tags.add(to_add.club)

        else:
            to_add = view_post.parent
            nomi.nomi_approvals.add(to_add)
            nomi.tags.add(to_add.club)
        return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def nomi_reject(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post(request, nomi_pk)

    if access:
        to_remove = view_post
        nomi.nomi_approvals.remove(to_remove)
        return HttpResponseRedirect(reverse('post_view', kwargs={'pk': view_post.pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def final_nomi_approval(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post(request, nomi_pk)

    if access and (view_post.perms == "can ratify the post" or view_post.perms =="can approve post and send nominations to users") :
        if view_post.elder_brother:
            to_add = view_post.elder_brother
            nomi.nomi_approvals.add(to_add)
            nomi.tags.add(to_add.club)

        if view_post.parent:
            to_add = view_post.parent
            nomi.nomi_approvals.add(to_add)
            nomi.tags.add(to_add.club)

        nomi.open_to_users()
        return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': nomi_pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def copy_nomi_link(request, pk):
    url = DOMAIN_NAME + '/nominations/nomi_detail/' + str(pk) + '/'
    pyperclip.copy(url)

    return HttpResponseRedirect(reverse('admin_portal'))
