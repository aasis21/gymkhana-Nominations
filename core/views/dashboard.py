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
from forms.views import replicate\
# from gymkhanaNominations import DOMAIN_NAME
from core.models import *
from core.forms import *
from core.scraper import getRecord



############################################     DASHBOARD VIEWS     ###################################################
## ------------------------------------------------------------------------------------------------------------------ ##


# main index view for user,contains all nomination to be filled by normal user,
# have club filter that filter both nomination and its group..
# is_safe
@login_required
def index(request):
    if request.user.is_authenticated:
        try:
            today = datetime.now()
            posts = Post.objects.filter(post_holders=request.user)
            username = UserProfile.objects.get(user=request.user)
            club_filter = ClubFilter(request.POST or None)
            if club_filter.is_valid():
                if club_filter.cleaned_data['club'] == 'NA':
                    club_filter = ClubFilter
                    grouped_nomi = GroupNomination.objects.filter(status='out')
                    nomi = Nomination.objects.filter(group_status='normal').filter(status='Nomination out')
                    re_nomi = Nomination.objects.filter(group_status='normal'). \
                        filter(status='Interview period and Nomination reopened')
                    nomi = nomi | re_nomi

                    result_query = sorted(chain(nomi, grouped_nomi), key=attrgetter('opening_date'), reverse=True)

                    return render(request, 'index1.html', context={'posts': posts, 'username': username,
                                                                   'club_filter': club_filter, 'today': today,
                                                                   'result_query': result_query})



                club = Club.objects.get(pk=club_filter.cleaned_data['club'])
                grouped_nomi = club.club_group.all().filter(status='out')
                nomi = club.club_nomi.all().filter(group_status='normal').filter(status='Nomination out')
                re_nomi = club.club_nomi.all().filter(group_status='normal').\
                    filter(status='Interview period and Nomination reopened')
                nomi = nomi | re_nomi
                result_query = sorted(chain(nomi, grouped_nomi), key=attrgetter('opening_date'), reverse=True)


                return render(request, 'index1.html', context={'posts': posts, 'username': username,
                                                               'result_query': result_query, 'club_filter': club_filter,
                                                               'today': today})

            grouped_nomi = GroupNomination.objects.filter(status='out')
            nomi = Nomination.objects.filter(group_status='normal').filter(status='Nomination out')
            re_nomi = Nomination.objects.filter(group_status='normal').\
                filter(status='Interview period and Nomination reopened')
            nomi = nomi | re_nomi

            result_query = sorted(chain(nomi, grouped_nomi), key=attrgetter('opening_date'), reverse=True)


            return render(request, 'index1.html', context={'posts': posts, 'username': username,
                                                           'club_filter': club_filter, 'today': today,
                                                           'result_query': result_query})

        except ObjectDoesNotExist:
            form = UserId(request.POST or None)
            if form.is_valid():
                try:
                    data = getRecord(form.cleaned_data['user_roll'])
                    
                except:
                    error = True
                    return render(request, 'register.html', context={'form': form, 'error': error})

                email = str(request.user) + '@iitk.ac.in'
                if email == data['email']:
                    profile = UserProfile.objects.create(user=request.user,name = data['name'],roll_no = data['roll'],
                                                     programme = data["program"],department = data['department'],
                                                     contact = data['mobile'], room_no = data['room'],hall = data['hall'])

                    pk = profile.pk
                    return HttpResponseRedirect(reverse('profile_update', kwargs={'pk': pk}))

                else:
                    error = True
                    return render(request, 'register.html', context={'form': form, 'error': error})

            error = False
            return render(request, 'register.html', context={'form': form ,'error':error})

    else:
        return HttpResponseRedirect(reverse('login'))


# contain all nomination for which user have rights whether created by him or created by his chil post
# also shows nomination for which he has been added as interview panel
# is_safe
@login_required
def admin_portal(request):
    posts = Post.objects.filter(post_holders=request.user)
    username = UserProfile.objects.get(user=request.user)

    admin_query = Nomination.objects.none()

    for post in posts:
        query = Nomination.objects.filter(nomi_approvals=post)
        admin_query = admin_query | query

    panel_nomi = request.user.panel.all().exclude(status='Nomination created')

    admin_query = admin_query | panel_nomi

    admin_query = admin_query.distinct().exclude(status='Work done')
    admin_query_reverse = admin_query[::-1]

    club_filter = ClubFilter(request.POST or None)
    if club_filter.is_valid():
        club = Club.objects.get(pk=club_filter.cleaned_data['club'])
        admin_query = admin_query.filter(tags=club)
        admin_query_reverse = admin_query[::-1]

        return render(request, 'admin_portal.html', context={'posts': posts, 'username': username,
                                                             'admin_query': admin_query_reverse,
                                                             'club_filter': club_filter})

    return render(request, 'admin_portal.html', context={'posts': posts, 'username': username,
                                                         'admin_query': admin_query_reverse,
                                                         'club_filter': club_filter})



# a view for retification purpose
# is_safe
@login_required
def senate_view(request):
    nomi_ratify = Nomination.objects.filter(status='Sent for ratification')
    all_posts = Post.objects.filter(post_holders=request.user)
    access = False

    for post in all_posts:
        if post.perms == 'can ratify the post':
            access = True
            break

    if access:
        return render(request, 'senate_view.html', context={'nomi': nomi_ratify})

    else:
        return render(request, 'no_access.html')


@login_required
def interview_list(request):
    interviews = Nomination.objects.filter(interview_panel=request.user).exclude(status = 'Work done')

    return render(request, 'interviews.html', context={'interviews': interviews})
