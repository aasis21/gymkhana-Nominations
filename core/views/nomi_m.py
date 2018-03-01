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
from .nomi_cr import get_access_and_post_for_result,get_access_and_post



## ------------------------------------------------------------------------------------------------------------------ ##
#########################################    NOMINATION MONITOR VIEWS   ################################################
## ------------------------------------------------------------------------------------------------------------------ ##
# ****** in use...


@login_required
def nomi_apply(request, pk):
    nomination = Nomination.objects.get(pk=pk)
    count = NominationInstance.objects.filter(nomination=nomination).filter(user=request.user).count()
    tick = True
    if nomination.nomi_form:
        ct = nomination.nomi_form.question_set.count()
        tick = not ct


    if not count and (nomination.status == "Nomination out" or nomination.status =="Interview period and Nomination reopened"):
        if  not tick:
            questionnaire = nomination.nomi_form
            form = questionnaire.get_form(request.POST or None)
            form_confirm = SaveConfirm(request.POST or None)

            if form_confirm.is_valid():
                if form.is_valid():
                    filled_form = questionnaire.add_answer(request.user, form.cleaned_data)
                    if form_confirm.cleaned_data["save_or_submit"] == "only save":
                        NominationInstance.objects.create(user=request.user, nomination=nomination,
                                                          filled_form=filled_form,
                                                          submission_status=False, timestamp=date.today())
                        info = "Your application has been saved. It has not been submited. So make sure you submit it after further edits through your profile module"

                    else:
                        NominationInstance.objects.create(user=request.user, nomination=nomination, filled_form=filled_form,
                                                      submission_status = True,timestamp = date.today())
                        info = "Your application has been recorded. You can edit it through profile module."

                    return render(request, 'nomi_done.html', context={'info': info})

            return render(request, 'forms/show_form.html', context={'form': form, 'form_confirm': form_confirm,
                                                                    'questionnaire': questionnaire, 'pk': pk})
        else:
            questionnaire = nomination.nomi_form
            form_confirm = ConfirmApplication(request.POST or None)
            form = questionnaire.get_form(request.POST or None)
            if form_confirm.is_valid():
                NominationInstance.objects.create(user=request.user, nomination=nomination,submission_status = True,timestamp = date.today())
                info = "Your application has been recorded."
                return render(request, 'nomi_done.html', context={'info': info})

            return render(request, 'forms/show_form.html', context={'form': form,'form_confirm': form_confirm, 'pk': pk,'questionnaire': questionnaire})


    else:
        info = "You have applied for it already.You can edit it through profile module."

        if not (nomination.status == "Nomination out" or nomination.status =="Interview period and Nomination reopened"):
            info =  "Nomination has been closed"
        return render(request, 'nomi_done.html', context={'info': info})




def nomi_answer_edit(request, pk):
    application = NominationInstance.objects.get(pk=pk)
    nomination = application.nomination

    if application.user == request.user and (nomination.status == "Nomination out" or nomination.status =="Interview period and Nomination reopened") :
        ans_form = application.filled_form
        data = json.loads(ans_form.data)
        applicant = application.user.userprofile
        questionnaire = application.nomination.nomi_form
        form = questionnaire.get_form(request.POST or data)

        if nomination.nomi_form and application.submission_status== False:
            form_confirm = SaveConfirm(request.POST or None)
            if form_confirm.is_valid():
                if form.is_valid():
                    info = "Your application has been edited and saved locally. Don't forget to submit it before deadline "
                    if form_confirm.cleaned_data["save_or_submit"] == "save and submit":
                        application.submission_status = True
                        application.timestamp = date.today()
                        application.save()
                        info = "Your application has been edited and finally submitted."

                    json_data = json.dumps(form.cleaned_data)
                    ans_form.data = json_data
                    ans_form.save()
                    application.edit_time = date.today()
                    application.save()

                    return render(request, 'nomi_done.html', context={'info': info})


        else:
            form_confirm = ConfirmApplication(request.POST or None)


        if form_confirm.is_valid():
            if form.is_valid():
                json_data = json.dumps(form.cleaned_data)
                ans_form.data = json_data
                ans_form.save()
                application.edit_time = date.today()
                application.save()

                info = "Your application has been edited"
                return render(request, 'nomi_done.html', context={'info': info})

        return render(request, 'nomi_answer_edit.html', context={'form': form, 'form_confirm': form_confirm,
                                                                 'nomi': application, 'nomi_user': applicant})
    else:
        return render(request, 'no_access.html')


def get_mails(query_users):
    mail_ids = ''
    for each in query_users:
        if len(mail_ids):
            mail_ids = mail_ids + ', ' + str(each.user) + '@iitk.ac.in'
        else:
            mail_ids = str(each.user) + '@iitk.ac.in'

    return mail_ids

def get_nomi_status(nomination):
    status = [None] * 7

    if nomination.status == 'Nomination created':
        status[0] = True
    elif nomination.status == 'Nomination out':
        status[1] = True
    elif nomination.status == 'Interview period':
        status[2] = True
    elif nomination.status == 'Sent for ratification':
        status[3] = True
    elif nomination.status == 'Interview period and Reopening initiated':
        status[4] = True
    elif nomination.status == 'Interview period and Nomination reopened':
        status[5] = True
    else:
        status[6] = True

    return status

def get_accepted_csv(request,nomi_pk):
    # Create the HttpResponse object with the appropriate CSV header.
    nomination = Nomination.objects.get(pk=nomi_pk)
    accepted = NominationInstance.objects.filter(nomination=nomination).filter(status='Accepted')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="accepted.csv"'

    writer = csv.writer(response)

    writer.writerow([str(nomination.name),'SELECTED APPLICANTS', str(date.today())])
    writer.writerow(['S.No','Name', 'Email','Roll','Address','Contact'])
    i=1
    for each in accepted:
        try :
            profile = each.user.userprofile
            writer.writerow([str(i),each.user.userprofile,str(each.user)+'@iitk.ac.in',str(profile.roll_no),str(profile.room_no)+'/'+ str(profile.hall),str(profile.contact)])
        except:
            writer.writerow([str(i),each.user,str(each.user)+'@iitk.ac.in',str(each.start)])


        i = i + 1

    return response

@login_required
def applications(request, pk):
    nomination = Nomination.objects.get(pk=pk)
    applicants = NominationInstance.objects.filter(nomination=nomination).filter(submission_status = True)
    accepted = NominationInstance.objects.filter(nomination=nomination).filter(submission_status = True).filter(status='Accepted')
    rejected = NominationInstance.objects.filter(nomination=nomination).filter(submission_status = True).filter(status='Rejected')
    pending = NominationInstance.objects.filter(nomination=nomination).filter(submission_status = True).filter(status=None)

    mail_ids = [get_mails(applicants),get_mails(accepted),get_mails(rejected),get_mails(pending)]


    status = get_nomi_status(nomination)

    access, view_post = get_access_and_post_for_result(request, pk)
    if not access:
        access, view_post = get_access_and_post(request, pk)


    # if user post in parent tree
    if access:
        permission = None
        senate_permission = None

        if view_post.parent:
            if view_post.parent.perms == 'can ratify the post':
                permission = True
                senate_permission = False
        elif view_post.perms == 'can ratify the post':
            senate_permission = True
            permission = False

        # result approval things    can send,has been sent, can cancel
        results_approval = [None]*3

        if view_post in nomination.result_approvals.all():
            if view_post.parent in nomination.result_approvals.all():
                results_approval[1] = True
                grand_parent = view_post.parent.parent
                if grand_parent not in nomination.result_approvals.all():
                    results_approval[2] = True
            else:
                results_approval[0] = True


        if request.method == 'POST':
            reopen = DeadlineForm(request.POST)
            if reopen.is_valid():
                re_nomi = ReopenNomination.objects.create(nomi=nomination)
                re_nomi.approvals.add(view_post)
                nomination.deadline = reopen.cleaned_data['deadline']
                nomination.status = 'Interview period and Reopening initiated'
                nomination.save()
                return HttpResponseRedirect(reverse('nomi_detail', kwargs={'nomi_pk': pk}))
        else:
            reopen = DeadlineForm()



        form_confirm = ConfirmApplication(request.POST or None)
        if form_confirm.is_valid():
            nomination.status = 'Interview period'
            nomination.save()
            return HttpResponseRedirect(reverse('applicants', kwargs={'pk': pk}))



        return render(request, 'applicants.html', context={'nomination': nomination, 'applicants': applicants,
                                                           'form_confirm': form_confirm,'mail_ids':mail_ids,
                                                           'result_approval': results_approval,
                                                           'accepted': accepted, 'rejected': rejected, 'status': status,
                                                           'pending': pending, 'perm': permission,
                                                           'senate_perm': senate_permission,'reopen':reopen})



    ## if user in panel...
    if request.user in nomination.interview_panel.all():
        return render(request, 'applicant_panel.html', context={'nomination': nomination, 'applicants': applicants,
                                                                'accepted': accepted, 'rejected': rejected,
                                                                'pending': pending,  'status': status})

    if not access:
        return render(request, 'no_access.html')





@login_required
def nomination_answer(request, pk):
    application = NominationInstance.objects.get(pk=pk)
    ans_form = application.filled_form
    data = json.loads(ans_form.data)
    applicant = application.user.userprofile
    questionnaire = application.nomination.nomi_form
    form = questionnaire.get_form(data)

    comments = Commment.objects.filter(nomi_instance=application)
    comments_reverse = comments[::-1]
    comment_form = CommentForm(request.POST or None)

    nomination = application.nomination
    status = get_nomi_status(nomination)

    access = False
    access, view_post = get_access_and_post(request, nomination.pk)
    if not access:
        access, view_post = get_access_and_post_for_result(request, nomination.pk)

    all_posts = Post.objects.filter(post_holders=request.user)
    senate_perm = False
    for post in all_posts:
        if post.perms == 'can ratify the post':
            access = True
            senate_perm = True
            break



    if application.user == request.user:
        return render(request, 'nomi_answer_user.html', context={'form': form, 'nomi': application, 'nomi_user': applicant})




    if access or request.user in nomination.interview_panel.all():

         # result approval things    send,sent,cancel
        results_approval = [None]*3

        if view_post in nomination.result_approvals.all():
            if view_post.parent in nomination.result_approvals.all():
                results_approval[1] = True
                grand_parent = view_post.parent.parent
                if grand_parent not in nomination.result_approvals.all():
                    results_approval[2] = True
            else:
                results_approval[0] = True

        if request.user in nomination.interview_panel.all():
            view_post = nomination.nomi_post.parent
            if view_post.parent in nomination.result_approvals.all():
                results_approval[1] = True
                grand_parent = view_post.parent.parent
                if grand_parent not in nomination.result_approvals.all():
                    results_approval[2] = True
            else:
                results_approval[0] = True

        if comment_form.is_valid():
             Commment.objects.create(comments=comment_form.cleaned_data['comment'],
                                     nomi_instance=application, user=request.user)

             return HttpResponseRedirect(reverse('nomi_answer', kwargs={'pk': pk}))

        return render(request, 'nomi_answer.html', context={'form': form, 'nomi': application, 'nomi_user': applicant,
                                                            'comment_form': comment_form,
                                                            'comments': comments_reverse, 'senate_perm': senate_perm,
                                                             'status':status,
                                                            'result_approval': results_approval})
    else:
        return render(request, 'no_access.html')
