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
#########################################    POST RELATED VIEWS   ######################################################
## ------------------------------------------------------------------------------------------------------------------ ##

'''
a view for a given post....contains all things required for working on that post...
tips...use redirect if using form as button
is_safe
'''
@login_required
def post_view(request, pk):
    post = Post.objects.get(pk=pk)
    child_posts = Post.objects.filter(parent=post)
    child_posts_reverse = child_posts[::-1]

    post_approvals = Post.objects.filter(post_approvals=post).filter(status='Post created')
    post_to_be_approved = Post.objects.filter(take_approval = post).filter(status = 'Post created')
    post_count = post_to_be_approved.count()
    post_approvals = post_to_be_approved|post_approvals
    post_approvals = post_approvals.distinct()

    entity_approvals = ClubCreate.objects.filter(take_approval=post)
    entity_by_me = ClubCreate.objects.filter(requested_by=post)

    nomi_approvals = Nomination.objects.filter(nomi_approvals=post).filter(status='Nomination created').filter(group_status= 'normal')
    re_nomi_approval = ReopenNomination.objects.filter(approvals=post).\
        filter(nomi__status='Interview period and Reopening initiated')
    group_nomi_approvals = GroupNomination.objects.filter(status='created').filter(approvals=post)
    count = nomi_approvals.count() + group_nomi_approvals.count() + re_nomi_approval.count()

    result_approvals = Nomination.objects.filter(result_approvals=post).exclude(status='Work done').\
        exclude(status='Nomination created').exclude(status='Nomination out')
    to_deratify = Deratification.objects.filter(deratify_approval = post).exclude(status = 'deratified')

    if request.method == 'POST':
        tag_form = ClubForm(request.POST)
        if tag_form.is_valid():
            if post.perms == "can ratify the post":
                Club.objects.create(club_name=tag_form.cleaned_data['club_name'], club_parent=post.club)
            else:
                ClubCreate.objects.create(club_name=tag_form.cleaned_data['club_name'], club_parent=post.club,
                                          take_approval=post.parent, requested_by=post)
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': pk}))

    else:
        tag_form = ClubForm



    if request.user in post.post_holders.all():
        return render(request, 'post1.html', context={'post': post, 'child_posts': child_posts_reverse,
                                                      'post_approval': post_approvals, 'tag_form': tag_form,
                                                      'nomi_approval': nomi_approvals,
                                                      'group_nomi_approvals': group_nomi_approvals,
                                                      'entity_by_me': entity_by_me, 're_nomi_approval': re_nomi_approval,
                                                      'result_approvals': result_approvals, 'count': count,
                                                      "to_deratify": to_deratify, "post_count": post_count,
                                                      'entity_approvals': entity_approvals})
    else:
        return render(request, 'no_access.html')


@login_required
def add_post_holder(request, pk):   # pk of the Post
    post = Post.objects.get(pk=pk)

    if request.method == 'POST':
        post_holder_Form = PostHolderForm(request.POST)
        if post_holder_Form.is_valid():
            email = post_holder_Form.cleaned_data['email']
            start_year = post_holder_Form.cleaned_data['session']

            try:
                name = User.objects.get(username=email)
                post.post_holders.add(name)
                session = Session.objects.filter(start_year=start_year).first()
                if session is None:
                    session = Session.objects.create(start_year=start_year)

                previous_history = PostHistory.objects.filter(post = post).filter(user = name).filter(post_session = session)

                if not previous_history:
                    PostHistory.objects.create(post=post, user=name, post_session=session,
                                             end=session_end_date(session.start_year))

                return HttpResponseRedirect(reverse('child_post', kwargs={'pk': pk}))



            except ObjectDoesNotExist:
                return render(request, 'add_post_holder.html', context={'post': post, 'form': post_holder_Form})

    else:
        post_holder_Form = PostHolderForm
        return render(request, 'add_post_holder.html', context={'post': post, 'form': post_holder_Form})


'''
view to create a new post, a child post for a post can be created only by the post holders of that post...
is_safe parent is simply added ,goes directly to parent for approval
'''
@login_required
def post_create(request, pk):
    parent = Post.objects.get(pk=pk)
    if request.method == 'POST':
        post_form = PostForm(parent, request.POST)
        if post_form.is_valid():
            club_id = post_form.cleaned_data['club']
            club = Club.objects.get(pk=club_id)
            post = Post.objects.create(post_name=post_form.cleaned_data['post_name'], club=club, parent=parent,elder_brother= parent)
            post.take_approval = parent.parent
            post.post_approvals.add(parent.parent)
            post.save()
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': pk}))

    else:
        club = parent.club
        post_form = PostForm(parent)

    if request.user in parent.post_holders.all():
        return render(request, 'nomi/post_form.html', context={'form': post_form, 'parent': parent})
    else:
        return render(request, 'no_access.html')




@login_required
def senate_post_create(request, pk):
    parent = Post.objects.get(pk=pk)
    if request.method == 'POST':
        post_form = PostForm(parent, request.POST)
        if post_form.is_valid():
            club_id = post_form.cleaned_data['club']
            club = Club.objects.get(pk=club_id)
            elder_brother_id = post_form.cleaned_data['elder_brother']
            elder_brother = Post.objects.get(pk=elder_brother_id)
            Post.objects.create(post_name=post_form.cleaned_data['post_name'],
                                elder_brother=elder_brother, club=club, parent=parent,
                                perms=post_form.cleaned_data['power'], status='Post approved')

            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': pk}))

    else:
        club = parent.club
        post_form = PostForm(parent)

    if request.user in parent.post_holders.all():
        return render(request, 'nomi/post_form.html', context={'form': post_form, 'parent': parent})
    else:
        return render(request, 'no_access.html')


# only parent post have access to this view
# is_safe
@login_required
def child_post_view(request, pk):
    post = Post.objects.get(pk=pk)
    parent = post.parent
    nominations = Nomination.objects.filter(nomi_post=post)



    give_form = BlankForm(request.POST or None)
    if give_form.is_valid():
        if post.tag_perms == 'normal':
            post.tag_perms = 'Can create'
        else:
            post.tag_perms = 'normal'

        post.save()
        return HttpResponseRedirect(reverse('child_post', kwargs={'pk': pk}))

    if request.user in parent.post_holders.all():
        return render(request, 'child_post1.html', {'post': post, 'nominations': nominations, 'parent':parent,
                                                     'give_form': give_form})
    else:
        return render(request, 'no_access.html')

# the viewer_post which have access add its parent for approval of post and also add parent club as post tag..
# is_safe
@login_required
def post_approval(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    access = False
    if request.user in post.take_approval.post_holders.all():
        access = True


    if access:
        if post.take_approval.perms == "can ratify the post":
            post.status = 'Post approved'
            post.save()
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': post.take_approval.pk}))
        else:
            to_add = post.take_approval.parent
            current = post.take_approval
            post.post_approvals.add(to_add)
            post.tags.add(to_add.club)
            post.take_approval = to_add
            post.save()
            return HttpResponseRedirect(reverse('post_view', kwargs={'pk': current.pk}))
    else:
        return render(request, 'no_access.html')


def edit_post_name(request,post_pk):
    post = Post.objects.get(pk=post_pk)
    access = False
    if request.user in post.take_approval.post_holders.all():
        access = True

    if access:
        if request.method == 'POST':
            edit_post  = ChangePostName(request.POST)
            if edit_post.is_valid():
                post.post_name = edit_post.cleaned_data['post_name']
                post.save()
                return HttpResponseRedirect(reverse('edit_post_name', kwargs={'post_pk': post_pk}))


        else:
            edit_post = ChangePostName

        return render(request, 'edit_post_name.html', {'post': post,  'edit_post': edit_post})
    else:
        return render(request, 'no_access.html')




# the viewer removes himself from approvals ,thus delete the post down...
# is_safe
@login_required
def post_reject(request, post_pk):
    post = Post.objects.get(pk=post_pk)

    access = False
    if request.user in post.take_approval.post_holders.all():
        access = True
        view = post.take_approval


    if access:
        post.delete()
        return HttpResponseRedirect(reverse('post_view', kwargs={'pk': view.pk}))
    else:
        return render(request, 'no_access.html')
