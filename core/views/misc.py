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



@login_required
def ratify(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post_for_result(request,nomi_pk)

    if access:
        if  view_post.perms == "can ratify the post":
            nomi.append()
            return HttpResponseRedirect(reverse('applicants', kwargs={'pk': nomi_pk}))
        else:
            return render(request, 'no_access.html')
    else:
        return render(request, 'no_access.html')


@login_required
def request_ratify(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post_for_result(request,nomi_pk)

    if access:
        if view_post.parent:
            to_add = view_post.parent
            nomi.result_approvals.add(to_add)
            nomi.nomi_approvals.add(to_add)
        nomi.status = 'Sent for ratification'
        nomi.save()

        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': nomi_pk}))

    else:
        return render(request, 'no_access.html')


@login_required
def cancel_ratify(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post_for_result(request,nomi_pk)

    if access:
        if view_post.parent:
            to_remove = view_post.parent
            nomi.result_approvals.remove(to_remove)
            nomi.nomi_approvals.remove(to_remove)
        nomi.status = 'Interview period'
        nomi.save()

        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': nomi_pk}))

    else:
        return render(request, 'no_access.html')


@login_required
def cancel_result_approval(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post_for_result(request,nomi_pk)

    if access:
        to_remove = view_post.parent
        if to_remove.parent not in nomi.result_approvals.all():
            nomi.result_approvals.remove(to_remove)
        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': nomi_pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def result_approval(request, nomi_pk):
    nomi = Nomination.objects.get(pk=nomi_pk)
    access, view_post = get_access_and_post_for_result(request,nomi_pk)

    if access:
        if view_post == nomi.nomi_post.parent:
            nomi.show_result = True

        to_add = view_post.parent
        nomi.result_approvals.add(to_add)
        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': nomi_pk}))
    else:
        return render(request, 'no_access.html')

@login_required
def create_deratification_request(request, post_pk, user_pk ,type):
    post = Post.objects.get(pk=post_pk)
    user =User.objects.get(pk=user_pk)

    if request.user in post.parent.post_holders.all():
        Deratification.objects.create(name=user, post=post,status = type, deratify_approval=post.parent)


    return HttpResponseRedirect(reverse('child_post', kwargs={'pk': post_pk}))


@login_required
def approve_deratification_request(request,pk):
    to_deratify = Deratification.objects.get(pk = pk)
    view = to_deratify.deratify_approval
    if request.user in view.post_holders.all():
        if view.perms == "can ratify the post":
             to_deratify.post.post_holders.remove(to_deratify.name)
             history=PostHistory.objects.filter(user=to_deratify.name).filter(post = to_deratify.post).first()
             if to_deratify.status=='remove from post':
                 history.delete()
                 to_deratify.status = 'removed'

             else:
                 history.end = date.today()
                 history.save()
                 to_deratify.status = 'deratified'

             to_deratify.save()

        else:
            to_deratify.deratify_approval = view.parent
            to_deratify.save()

        return HttpResponseRedirect(reverse('post_view', kwargs={'pk':view.pk}))
    else:
        return render(request, 'no_access.html')




@login_required
def reject_deratification_request(request, pk):
    to_deratify = Deratification.objects.get(pk=pk)
    view = to_deratify.deratify_approval
    if request.user in view.post_holders.all():
        to_deratify.delete()
        return HttpResponseRedirect(reverse('post_view', kwargs={'pk':view.pk}))
    else:
        return render(request, 'no_access.html')



'''
mark_as_interviewed, reject_nomination, accept_nomination: Changes the interview status/ nomination_instance status
of the applicant
'''

def get_access_and_post_for_selection(request, nomi_pk):
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
def mark_as_interviewed(request, pk):

    application = NominationInstance.objects.get(pk=pk)
    id_nomi = application.nomination.pk
    nomination = Nomination.objects.get(pk=id_nomi)
    access, view_post = get_access_and_post_for_selection(request,id_nomi)
    if access or request.user in nomination.interview_panel.all():
        application.interview_status = 'Interview Done'
        application.save()
        return HttpResponseRedirect(reverse('nomi_answer', kwargs={'pk': pk}))
    else:
        return render(request, 'no_access.html')


@login_required
def accept_nomination(request, pk):
    application = NominationInstance.objects.get(pk=pk)
    id_accept = application.nomination.pk
    nomination = Nomination.objects.get(pk=id_accept)
    access, view_post = get_access_and_post_for_selection(request, id_accept)
    if access or request.user in nomination.interview_panel.all():
        application.status = 'Accepted'
        application.save()

        comment = '<strong>' + str(request.user.userprofile.name) + '</strong>' + ' Accepted '\
                  + '<strong>' + str(application.user.userprofile.name) + '</strong>'
        status = Commment.objects.create(comments=comment, nomi_instance=application)

        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': id_accept}))
    else:
        return render(request, 'no_access.html')




@login_required
def reject_nomination(request, pk):
    application = NominationInstance.objects.get(pk=pk)
    id_reject = application.nomination.pk
    nomination = Nomination.objects.get(pk=id_reject)
    access, view_post = get_access_and_post_for_selection(request, id_reject)
    if access or request.user in nomination.interview_panel.all():
        application.status = 'Rejected'
        application.save()

        comment = '<strong>' + str(request.user.userprofile.name) + '</strong>' + ' Rejected ' \
                  + '<strong>' + str(application.user.userprofile.name) + '</strong>'
        status = Commment.objects.create(comments=comment, nomi_instance=application)

        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': id_reject}))
    else:
        return render(request, 'no_access.html')


'''
append_user, replace_user: Adds and Removes the current post-holders according to their selection status
'''

@login_required
def append_user(request, pk):
    posts = request.user.posts.all()
    access = False
    for post in posts:
        if post.perms == "can ratify the post":
            access = True
            break

    if access:
        nomi = Nomination.objects.get(pk=pk)
        nomi.append()
        return HttpResponseRedirect(reverse('applicants', kwargs={'pk': pk}))
    else:
        return render(request, 'no_access.html')



@login_required
def end_tenure(request):
    posts = request.user.posts.all()
    access = False
    for post in posts:
        if post.perms == "can ratify the post":
            access = True
            break
    if access:
        posts = Post.objects.all()
        for post in posts:
            for holder in post.post_holders.all():
                try:
                    history = PostHistory.objects.get(post=post, user=holder)
                    if history.end:
                        if date.today() >= history.end:
                            post.post_holders.remove(holder)

                except ObjectDoesNotExist:
                    pass

        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'no_access.html')


    # Import all posts of all clubs
    # Check if their session has expired (31-3-2018 has passed)
    # Remove them from the post
    # Create the post history (No need, its already created)

## ------------------------------------------------------------------------------------------------------------------ ##
############################################       PROFILE VIEWS      ##################################################
## ------------------------------------------------------------------------------------------------------------------ ##


@login_required
def profile_view(request):
    pk = request.user.pk

    my_posts = Post.objects.filter(post_holders=request.user)
    history = PostHistory.objects.filter(user=request.user).order_by('start')

    pending_nomi = NominationInstance.objects.filter(user=request.user).filter(nomination__status='Nomination out')
    pending_re_nomi = NominationInstance.objects.filter(user=request.user).\
        filter(nomination__status='Interview period and Nomination reopened')
    pending_nomi = pending_nomi | pending_re_nomi

    # show the instances that user finally submitted.. not the saved one
    interview_re_nomi = NominationInstance.objects.filter(user=request.user).filter(submission_status = True).filter(nomination__status='Interview period and Reopening initiated')
    interview_nomi = NominationInstance.objects.filter(user=request.user).filter(submission_status = True).filter(nomination__status='Interview period')

    interview_nomi = interview_nomi | interview_re_nomi

    declared_nomi = NominationInstance.objects.filter(user=request.user).filter(submission_status = True).filter(nomination__status='Sent for ratification')


    try:
        user_profile = UserProfile.objects.get(user__id=pk)
        post_exclude_history = []    # In case a post is not registered in history

        post_history = []
        for his in history:
            post_history.append(his.post)

        for post in my_posts:
            if post not in post_history:
                post_exclude_history.append(post)

        return render(request, 'profile.html', context={'user_profile': user_profile, 'history': history,
                                                        'pending_nomi': pending_nomi, 'declared_nomi': declared_nomi,
                                                        'interview_nomi': interview_nomi, 'my_posts': my_posts,
                                                        'excluded_posts': post_exclude_history})

    except ObjectDoesNotExist:
        return HttpResponseRedirect('create')


@login_required
def public_profile(request, pk):
    student = UserProfile.objects.get(pk=pk)
    student_user = student.user
    history = PostHistory.objects.filter(user=student_user)
    my_posts = Post.objects.filter(post_holders=student_user)

    return render(request, 'public_profile.html', context={'student': student, 'history': history,
                                                           'my_posts': my_posts})



def UserProfileUpdate(request,pk):
    profile = UserProfile.objects.get(pk = pk)
    if profile.user == request.user:

        form = ProfileForm(request.POST or None, instance=profile)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('profile'))

        return render(request, 'nomi/userprofile_form.html', context={'form': form})
    else:
        return render(request, 'no_access.html')



class CommentUpdate(UpdateView):
    model = Commment
    fields = ['comments']

    def get_success_url(self):
        form_pk = self.kwargs['form_pk']
        return reverse('nomi_answer', kwargs={'pk': form_pk})


class CommentDelete(DeleteView):
    model = Commment

    def get_success_url(self):
        form_pk = self.kwargs['form_pk']
        return reverse('nomi_answer', kwargs={'pk': form_pk})


def all_nominations(request):
    all_nomi = Nomination.objects.all().exclude(status='Nomination created')

    return render(request, 'all_nominations.html', context={'all_nomi': all_nomi})
