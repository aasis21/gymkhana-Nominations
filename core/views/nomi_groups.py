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
#########################################     GROUP NOMINATION VIEWS    ################################################
## ------------------------------------------------------------------------------------------------------------------ ##


@login_required
def group_nominations(request, pk):
    post = Post.objects.get(pk=pk)
    child_posts = Post.objects.filter(parent=post)
    child_posts_reverse = child_posts[::-1]
    post_approvals = Post.objects.filter(post_approvals=post).filter(status='Post created')
    nomi_approvals = Nomination.objects.filter(nomi_approvals=post).filter(status='Nomination created')

    if request.user in post.post_holders.all():
        if request.method == 'POST':
            groupform = SelectNomiForm(post, request.POST)
            group_detail = GroupDetail(request.POST)
            if group_detail.is_valid():
                if groupform.is_valid():
                    group = group_detail.save()
                    group.approvals.add(post)
                    for nomi_pk in groupform.cleaned_data['group']:
                        # tasks to be performed on nomination
                        nomi = Nomination.objects.get(pk=nomi_pk)
                        group.nominations.add(nomi)
                        for tag in nomi.tags.all():
                            group.tags.add(tag)
                        nomi.group_status = 'grouped'
                        if post.elder_brother:
                            to_add = post.elder_brother
                            nomi.nomi_approvals.add(to_add)
                        if group.deadline:
                            nomi.deadline = group.deadline
                        nomi.save()
                    return HttpResponseRedirect(reverse('post_view', kwargs={'pk': pk}))

        else:
            group_detail= GroupDetail
            groupform = SelectNomiForm(post)

        return render(request, 'nomi_group.html', context={'post': post, 'child_posts': child_posts_reverse,
                                                           'post_approval': post_approvals, 'nomi_approval': nomi_approvals,
                                                           'form': groupform, 'title_form': group_detail})
    else:
        return render(request, 'no_access.html')


@login_required
def group_nomi_detail(request, pk):
    group_nomi = GroupNomination.objects.get(pk=pk)
    admin = 0
    for post in request.user.posts.all():
        if post in group_nomi.approvals.all():
            admin = post

    form_confirm = ConfirmApplication(request.POST or None)
    if form_confirm.is_valid():
        for nomi in group_nomi.nominations.all():
            nomi.open_to_users()
        group_nomi.status = 'out'
        group_nomi.save()

    return render(request, 'group_detail.html', {'group_nomi': group_nomi, 'admin': admin,
                                                 'form_confirm': form_confirm})


@login_required
def edit_or_add_to_group(request, pk, gr_pk):
    post = Post.objects.get(pk=pk)
    group = GroupNomination.objects.get(pk=gr_pk)

    if request.user in post.post_holders.all() and post in group.approvals.all():
        group_detail = GroupDetail(request.POST or None, instance=group)
        if group_detail.is_valid():
            group_detail.save()
        if request.method == 'POST':
            groupform = SelectNomiForm(post, request.POST)

            if groupform.is_valid():

                for nomi_pk in groupform.cleaned_data['group']:
                    # things to be performed on nomination
                    nomi = Nomination.objects.get(pk=nomi_pk)
                    group.nominations.add(nomi)
                    for tag in nomi.tags.all():
                        group.tags.add(tag)
                    nomi.group_status = 'grouped'
                    if post.elder_brother:
                        to_add = post.elder_brother
                        nomi.nomi_approvals.add(to_add)
                    if group.deadline:
                        nomi.deadline = group.deadline

                    nomi.save()
                return HttpResponseRedirect(reverse('group_nomi_detail', kwargs={'pk': gr_pk}))

        else:
            groupform = SelectNomiForm(post)

        return render(request, 'nomi_group.html', context={'post': post,'form': groupform, 'title_form': group_detail})
    else:
        return render(request, 'no_access.html')



@login_required
def remove_from_group(request, nomi_pk, gr_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    group = GroupNomination.objects.get(pk=gr_pk)
    group.nominations.remove(nomi)

    nomi.group_status = 'normal'
    nomi.status = 'Nomination created'
    nomi.save()

    return HttpResponseRedirect(reverse('group_nomi_detail', kwargs={'pk': gr_pk}))
