from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404, render
from django.template import loader
from django.contrib import messages
from django.conf import settings
import collections
from django.core.mail import send_mail
from django.template import loader
import json
from datetime import datetime
from .forms import  UserUpdateForm as userupdateform
from .forms import  ProfileUpdateForm as profile_update_form
import urllib
from linkup.constants import PrivacyChoices, StateChoices
from linkup.models import (
    Event,
    Poll,
    UserPollChoice,
    PollChoice,
    DatetimeChoice,
    LocationChoice,
    UserEventChoice,

)

from .constants import (
    event_category_choices,
    event_importance_choices,
    privacy_choices,
)
def return_statistics():
    polls_count = Poll.objects.count()
    events_count = Event.objects.count()
    users_count = User.objects.count()
    return {
        'polls_count': polls_count,
        'events_count': events_count,
        'users_count': users_count
    }

# Index page function
def index(request):
    template = loader.get_template('index.html')
    context = {
        'title': 'Link Up'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# About page function
def about(request):
    template = loader.get_template('about.html')
    context = {
        'title': 'About'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# EVENT FUNCTIONS ###

# Datetime duration Function
# It takes two arguments and return a string
def period(d1, d2):
        s1 = d1[:10]
        s2 = d2[:10]
        start= d1[11:]
        end= d2[11:]

        d1 = datetime.strptime(s1, "%d/%m/%Y")
        d2 = datetime.strptime(s2, "%d/%m/%Y")
        d = abs((d2 - d1).days)
        start_dt = datetime.strptime(start, '%H:%M')
        end_dt = datetime.strptime(end, '%H:%M')
        diff = (end_dt - start_dt)
        diff = str(diff)
        if diff[0] == '-':
            if diff[12].isdigit():
                diff = diff[8:13]
            else:
                diff = diff[8:12]
        else:
            if start[0:2] =='00':
                if diff[1].isdigit():
                    diff = diff[:5]
                else:
                    diff = diff[:4]
            else:
                diff = diff[:5]
        if diff[0:2].isdigit():
            diff = f'{diff[0:2]}h {diff[3:]}m'
        else:
            diff = f'{diff[0:1]}h {diff[2:4]}m'

        if diff.find('00m') != -1:
            diff = diff[:diff.find('00')]
        if diff.find('0h') != -1:
            diff = diff[diff.find('0h')+2:]
        if d !=0:
            if diff.isspace() :
                return (f'{d} days')
            else:
                return (f'{d} days,{diff}')
        else:
            return (f'{diff}')

# Event List Function
# Return Event list page with paginator to 10 per page
def event_list(request):
    events = Event.objects.all()
    template = loader.get_template('event_list.html')
    paginator = Paginator(events, 10)
    page = request.GET.get('page', 1)
    events = paginator.get_page(page)
    context = {
        'data': events,
        'title': 'Link Up Event List'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# Result Event Funtion
# Return The actual result or an event
def result (request, pk=None):
    event = get_object_or_404(Event, pk=pk)
    template = loader.get_template('event_detail/result.html')
    options = []
    datetime_choices = DatetimeChoice.objects.filter(event=event)
# Used to create the table to display event details
    for d in datetime_choices:
        option = {"content":"", "period":'',"users":[], "count":''}
        persons = []
        for x in UserEventChoice.objects.filter(event=event, datetime_choices=d):
            persons.append(x.creator.username)
        option['content'] = d.content
        try:
            s1 = str(d.content)
            option['period'] = period(s1[:s1.find('-')-1],s1[s1.find('-')+2:])
        except:
            option['period'] = ''
        option['users'] = persons
        option['count'] = len(persons)
        options.append(option)
    context = {
        'event': event,
        'options':options
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))


# Event detail Function
# Returns the event details relating to event stage
def event_detail(request, pk=None):
    event = get_object_or_404(Event, pk=pk)
    if event.privacy == PrivacyChoices.PRIVATE:
        if (request.user in event.invited_users.all()) or (request.user == event.creator or request.user.is_superuser):
            if event.state == StateChoices.OPENED:
                template = loader.get_template('event_detail/opened.html')
                datetime_choices = DatetimeChoice.objects.filter(event=event)
                options = []
                for d in datetime_choices:
                    try:
                        s1 = str(d.content)
                        option = {'pk':d.pk, 'content':d.content, 'period': period(s1[:s1.find('-')-1],s1[s1.find('-')+2:])}
                    except:
                        option = {'pk':d.pk, 'content':d.content, 'period':''}
                    options.append(option)
                context = {
                    'event': event,
                    'options': options
                }
                if request.user.id :
                    if UserEventChoice.objects.filter(creator=request.user, event=event).first() is not None:
                        context = {
                                    'event': event,
                                    'options': options,
                                    'btn':1,
                        }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))

            else:
                template = loader.get_template('event_detail/close.html')
                e = UserEventChoice.objects.filter(event=event)
                choices_list = []
                for i in e:
                    choice = {'datetime_choices' : i.datetime_choices.first().content,'location_choices':i.location_choices.first().content,'creator':i.creator.username}
                    choices_list.append(choice)
                ddd = [x['datetime_choices'] for x in choices_list]
                lll = [x['location_choices'] for x in choices_list]
                d = [item for item, count in collections.Counter(ddd).items() if count > 1]
                if len(d) != 0:
                    best_date = len([c for c in ddd if c ==[item for item, count in collections.Counter(ddd).items() if count > 1][0]])
                else:
                    best_date = 1
                l = [item for item, count in collections.Counter(lll).items() if count > 1]
                if len(l) != 0:
                    best_location = len([c for c in lll if c ==[item for item, count in collections.Counter(lll).items() if count > 1][0]])
                else:
                    best_location = 1
                template = loader.get_template('event_detail/close.html') # Outputs answers
                context = {
                'event': event,
                'best_date':best_date,
                'best_location':best_location
                }

                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
        else:
            messages.warning(request, 'This is a private event and you are not invited !')
            return redirect('event_list')

    elif event.privacy == PrivacyChoices.PUBLIC:
        if event.state == StateChoices.ClOSE:
            e = UserEventChoice.objects.filter(event=event)
            choices_list = []
            for i in e:
                choice = {'datetime_choices' : i.datetime_choices.first().content,'location_choices':i.location_choices.first().content,'creator':i.creator.username}
                choices_list.append(choice)
            ddd = [x['datetime_choices'] for x in choices_list]
            lll = [x['location_choices'] for x in choices_list]
            d = [item for item, count in collections.Counter(ddd).items() if count > 1]
            if len(d) != 0:
                best_date = len([c for c in ddd if c ==[item for item, count in collections.Counter(ddd).items() if count > 1][0]])
            else:
                best_date = 1
            l = [item for item, count in collections.Counter(lll).items() if count > 1]
            if len(l) != 0:
                best_location = len([c for c in lll if c ==[item for item, count in collections.Counter(lll).items() if count > 1][0]])
            else:
                best_location = 1
            template = loader.get_template('event_detail/close.html')
            context = {
            'event': event,
            'best_date':best_date,
            'best_location':best_location
            }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
        else:
            template = loader.get_template('event_detail/opened.html')
            datetime_choices = DatetimeChoice.objects.filter(event=event)
            options = []
            for d in datetime_choices:
                try:
                    s1 = str(d.content)
                    option = {'pk':d.pk, 'content':d.content, 'period': period(s1[:s1.find('-')-1],s1[s1.find('-')+2:])}
                except:
                    option = {'pk':d.pk, 'content':d.content, 'period':''}
                options.append(option)
            context = {
                'event': event,
                'options': options
            }
            if request.user.id :
                if UserEventChoice.objects.filter(creator=request.user, event=event).first() is not None:
                    context = {
                                'event': event,
                                'options': options,
                                'btn':1,
                    }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))

# Event create Function
# if request.user.id ==> registred user
# else ==> anonymous user
def event_new(request):
    if request.method == 'GET':
        template = loader.get_template('event_new.html')
        context = {
            'event_category_choices': event_category_choices,
            'event_importance_choices': event_importance_choices,
            'privacy_choices': privacy_choices
        }
        context.update(return_statistics())
        return HttpResponse(template.render(context, request))
    else:
        title = request.POST.get('title', None)
        description = request.POST.get('description', None)
        category = request.POST.get('category', None)
        importance = request.POST.get('importance', None)
        privacy = request.POST.get('privacy', None)
        datetime_choices = request.POST.getlist('ddd')
        datetime_choices = list(filter(None, datetime_choices))
        location_choices = request.POST.getlist('location')
        location_choices = list(filter(None, location_choices))
        invited_users = request.POST.getlist('invited')
        users = list(filter(None, invited_users))
        invalid_users = []
        for user in users:
            username = User.objects.filter(username=user).first()
            if username is None:
                invalid_users.append(user)
        if len(invalid_users)!=0:
            for usr in invalid_users:
                messages.warning(request, "{}, doesn't exit!".format(', '.join(invalid_users)))
                template = loader.get_template('event_new.html')
                invited_users = [ c for c in users]
                loc = [ c for c in location_choices]
                dat = [ c for c in datetime_choices]
                context = {
                    'event_category_choices': event_category_choices,
                    'event_importance_choices': event_importance_choices,
                    'privacy_choices': privacy_choices,
                    'title':title,
                    'description':description,
                    'datetime':dat,
                    'location':loc,
                    'invited_users':invited_users
            }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
        if title.isspace()==True or description.isspace()==True or (("".join(location_choices))=='') or (("".join(datetime_choices))==''):

            template = loader.get_template('event_new.html')
            invited_users = [ c for c in users]
            loc = [ c for c in location_choices]
            dat = [ c for c in datetime_choices]
            context = {
                'event_category_choices': event_category_choices,
                'event_importance_choices': event_importance_choices,
                'privacy_choices': privacy_choices,
                'title':title,
                'description':description,
                'datetime':dat,
                'location':loc,
            }
            context.update(return_statistics())
            messages.warning(request, 'Event creation unsuccessful!,'+'    '+' Please make sure all required information is entered')
            return HttpResponse(template.render(context, request))

        elif request.user.id:
            try:
                event = Event.objects.create(
                    title=title,
                    description=description,
                    category=category,
                    importance=importance,
                    privacy=privacy,
                    creator=request.user
                )

                for datetime_choice in datetime_choices:
                    if datetime_choice != '':
                        DatetimeChoice.objects.create(
                        content=datetime_choice,
                        event=event
                    )

                for location_choice in location_choices:
                    if location_choice != '':
                        LocationChoice.objects.create(
                        content=location_choice,
                        event=event
                        )
                if event.privacy == '0':
                    event.invited_users.add(request.user)
                    for invited_user in invited_users:
                        user = User.objects.filter(username=invited_user).first()
                        if user is not None:
                            event.invited_users.add(user)
                messages.success(request, 'Event creation successful!')
                return redirect('event_detail', pk=event.pk)
            except:
                messages.success(request, 'Event creation successful!')
                return redirect('event_detail', pk=event.pk)
        else:
                try:
                    event = Event.objects.create(
                        title=title,
                        description=description,
                        category=category,
                        importance=importance
                    )

                    for datetime_choice in datetime_choices:
                        if datetime_choice != '':
                            DatetimeChoice.objects.create(
                            content=datetime_choice,
                            event=event
                        )

                    for location_choice in location_choices:
                        if location_choice != '':
                            LocationChoice.objects.create(
                            content=location_choice,
                            event=event
                        )
                    if event.privacy == '0':
                        event.invited_users.add(request.user)
                        for invited_user in invited_users:
                            user = User.objects.filter(username=invited_user).first()
                            if user is not None:
                                event.invited_users.add(user)
                    messages.success(request, 'Event creation successful!')
                    return redirect('event_detail', pk=event.pk)
                except:
                    messages.success(request, 'Event creation successful!')
                    return redirect('event_detail', pk=event.pk)

# Event update Funtion
# Allows update of event prodivded user is either creator or admin (superuser)
def event_update(request,pk):
    event = get_object_or_404(Event, pk=pk)
    if  event.state == StateChoices.ClOSE or (request.user == event.creator or request.user.is_superuser )== False:
        messages.warning(request, 'Permission denied :/')
        return redirect('event_detail', pk=pk)
    else:
        if request.method == 'GET':
            e = DatetimeChoice.objects.filter(event=event)
            loc = LocationChoice.objects.filter(event=event)
            template = loader.get_template('event_update.html')
            invited_users = [ c for c in event.invited_users.all()]
            dat = [ c for c in e]
            context = {
                'event_category_choices': event_category_choices,
                'event_importance_choices': event_importance_choices,
                'privacy_choices': privacy_choices,
                'title':event.title,
                'datetime':dat,
                'description':event.description,
                'location':loc,
                'invited_users':invited_users

            }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
        else:
            title = request.POST.get('title', None)
            description = request.POST.get('description', None)
            category = request.POST.get('category', None)
            importance = request.POST.get('importance', None)
            privacy = request.POST.get('privacy', None)
            datetime_choices = request.POST.getlist('ddd')
            location_choices = request.POST.getlist('location')
            invited_users = request.POST.getlist('invited')
            if title.isspace()==True or description.isspace()==True or (("".join(location_choices))=='') or (("".join(datetime_choices))==''):
                messages.warning(request, 'Event update unsuccessful, Please make sure that all required information was entered !')
                e = DatetimeChoice.objects.filter(event=event)
                loc = LocationChoice.objects.filter(event=event)
                template = loader.get_template('event_update.html')
                invited_users = [ c for c in event.invited_users.all()]
                dat = [ c for c in e]
                context = {
                    'event_category_choices': event_category_choices,
                    'event_importance_choices': event_importance_choices,
                    'privacy_choices': privacy_choices,
                    'title':event.title,
                    'datetime':dat,
                    'description':event.description,
                    'location':loc,
                    'invited_users':invited_users

                }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))

            else:
                event = Event.objects.filter(pk=pk).update(
                        title=title,
                        description=description,
                        category=category,
                        importance=importance,
                        privacy=privacy,
                    )
                event = get_object_or_404(Event, pk=pk)
                DatetimeChoice.objects.filter(event=event).delete()
                for datetime_choice in datetime_choices:
                    if datetime_choice != '':
                        DatetimeChoice.objects.create(
                            content=datetime_choice,
                            event=event
                        )
                LocationChoice.objects.filter(event=event).delete()
                for location_choice in location_choices:
                    if location_choice != '':
                        LocationChoice.objects.create(
                            content=location_choice,
                            event=event
                        )

                event.invited_users.clear()
                if event.privacy == 0:
                    event.invited_users.add(request.user)
                    for invited_user in invited_users:
                        user = User.objects.filter(username=invited_user).first()
                        if user is not None:
                            event.invited_users.add(user)
                messages.success(request, 'Event update successful')
                return redirect('event_detail', pk=pk)


# Event close Function
# Allows users to close an event alongside sending notification email to participants
@login_required(login_url='/login/')
def event_close(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if  (event.state == StateChoices.ClOSE) or (request.user == event.creator or request.user.is_superuser )== False:
        messages.warning(request, 'No permission!')
        return redirect('event_detail', pk=pk)
    else:
        event.state = StateChoices.ClOSE
        event.save()
        messages.success(request, 'Event closed successful!')
        e = UserEventChoice.objects.filter(event=event)
        users = [x.creator for x in e]
        if users:
            for user in users:
                if user.email != '':
                    html_message = loader.render_to_string(
                    'mail_template.html',
                    {
                        'title':  event.title,
                        'type': 'event',
                        'link': f'http://127.0.0.1:8000/event/{event.pk}',
                    })
                    send_mail('Link Up Notification',event.title,settings.DEFAULT_FROM_EMAIL,[user.email],fail_silently=True,html_message=html_message)
                    # Above line sents the email

        return redirect('event_detail', pk=event.pk)




# Event Choice Function
# Allows event creator to view choices of ongoing/active event poll
def event_join(request, pk):
    if request.user.is_authenticated:
        if request.method == 'GET':
            event = get_object_or_404(Event, pk=pk)
            if UserEventChoice.objects.filter(creator=request.user, event=event).first() is not None:
                a = UserEventChoice.objects.filter(creator=request.user, event=event).all()
                for i in a:
                    for j in i.datetime_choices.all():
                        date = j.content
                    for j in i.location_choices.all():
                        loc = j.content
                event = get_object_or_404(Event, pk=pk)
                template = loader.get_template('event_detail/choices.html')
                try:
                    context = {'event': event,
                               'date':date,
                               'location':loc,
                               }
                except:
                    context = {'event': event
                           }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))

            template = loader.get_template('event_detail/join.html')
            context = {'event': event}
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
        elif request.method == 'POST':
            event = get_object_or_404(Event, pk=pk)
            datetime_choice_pks = request.POST.getlist('datetime')
            user_event_choice = UserEventChoice.objects.create(
                event=event,
                creator=request.user
            )
            for datetime_choice_pk in datetime_choice_pks:
                datetime_choice = get_object_or_404(DatetimeChoice, pk=datetime_choice_pk)
                user_event_choice.datetime_choices.add(datetime_choice)
            location_choice_pks = request.POST.getlist('location')
            for location_choice_pk in location_choice_pks:
                location_choice = get_object_or_404(LocationChoice, pk=location_choice_pk)
                user_event_choice.location_choices.add(location_choice)
            messages.success(request, 'Join to event successfully!')
            return redirect('event_detail', pk=pk)
    messages.warning(request, 'Please Log In to Join !')
    return redirect('event_detail', pk=pk)


# Event Submit Function
# Submission mechanismn
def event_submit(request):
    pk = request.POST.get('pk', False)

    event = get_object_or_404(Event, pk=pk)
    if request.method == 'GET':
            template = loader.get_template('event_detail/opened.html')
            context = {'event': event}
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
    else:
        if request.user.is_authenticated:
            if UserEventChoice.objects.filter(event=event, creator=request.user).count() != 0:
                messages.warning(request, 'Please do not submit your choices for this event again!')
                return redirect('event_detail', pk=pk)
            choice_pk = request.POST.get('choice',None)
            choice2_pk = request.POST.get('choice2', None)
            choice = get_object_or_404(DatetimeChoice, pk=choice_pk)
            choice2 = get_object_or_404(LocationChoice, pk=choice2_pk)
            user_event_choice = UserEventChoice.objects.create(
                    event=event,
                    creator=request.user)
            user_event_choice.datetime_choices.add(choice)
            user_event_choice.location_choices.add(choice2)
            messages.success(request, 'Your event submission was successful!')
            return redirect('event_detail', pk=pk)

        messages.warning(request, 'Please Log In to submit your choices !')
        return redirect('event_detail', pk=pk)

### POOL FUNCTIONS ###

# Poll List Function
# Return Poll list page with paginator to 10 per page
def poll_list(request):
    polls = Poll.objects.all()
    template = loader.get_template('poll_list.html')
    paginator = Paginator(polls, 5)
    page = request.GET.get('page')
    polls = paginator.get_page(page)
    context = {
        'data': polls,
        'title': 'Link Up Poll List'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# Result Poll Funtion
# Return The actual result for a Poll
def result_poll (request, pk=None):
    poll = get_object_or_404(Poll, pk=pk)
    template = loader.get_template('poll_detail/result.html')
    poll_choices = []
    items = PollChoice.objects.filter(poll=poll)
    for item in items:
        choice = {"option":item.content, "users":[], "count":0}
        k = 0
        c =  UserPollChoice.objects.filter(poll=poll,choices=item)
        for i in c:
            if i.get_full_name():
                choice["users"].append(i.get_full_name())
            else:
                k =k + 1
        choice["count"] = len(choice["users"])
        if k >0:
            choice["users"].append("Anonymous x"+str(k))
            choice["count"] = k + len(choice["users"])-1
        poll_choices.append(choice)

    context = {
        'poll': poll,
        'choices':poll_choices
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# Poll list Function
# Return the list of private polls
def poll_list_private(request):
    polls = Poll.objects.filter(privacy=0)
    template = loader.get_template('poll_list.html')
    paginator = Paginator(polls, 5)
    page = request.GET.get('page')
    polls = paginator.get_page(page)
    context = {
        'data': polls,
        'title': 'Link Up Private Poll List'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))



# Poll detail Function
# Return the detail page of an Poll relating with his state
def poll_detail(request, pk=None):
    poll = get_object_or_404(Poll, pk=pk)
    if poll.privacy == PrivacyChoices.PRIVATE:
        if (request.user in poll.invited_users.all()) or (request.user == poll.creator):
            if poll.state == StateChoices.OPENED:
                template = loader.get_template('poll_detail/opened.html')
                context = {'poll': poll}
                if request.user.is_authenticated:
                    a = UserPollChoice.objects.filter(poll=poll,creator=request.user).all()
                    mychoices = []
                    for i in a:
                        for j in i.choices.all():
                            mychoices.append(j)
                    context = {
                        'poll': poll,
                        'mychoices': mychoices
                    }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            else:
                template = loader.get_template('poll_detail/close.html')
                poll_choices = []
                items = PollChoice.objects.filter(poll=poll)
                for item in items:
                    choice = {"option":item.content, "users":[], "count":0}
                    k = 0
                    c =  UserPollChoice.objects.filter(poll=poll,choices=item)
                    for i in c:
                        if i.get_full_name():
                            choice["users"].append(i.get_full_name())
                        else:
                            k =k + 1
                    choice["count"] = len(choice["users"])
                    if k >0:
                        choice["users"].append("Anonymous x"+str(k))
                        choice["count"] = k + len(choice["users"])-1
                    poll_choices.append(choice)
                    best_option = max(x['count'] for x in poll_choices)
                context = {
                    'poll': poll,
                    'choices':poll_choices,
                    'best_option':best_option,
                }

                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
        else:
            messages.warning(request, 'This is a private poll and you are not invited !')
            from django.urls import resolve
            current_url = request.resolver_match.func.__name__
            redirect_to = request.META.get('HTTP_REFERER')
            return HttpResponseRedirect(redirect_to)

    elif poll.privacy == PrivacyChoices.PUBLIC:
        if poll.state == StateChoices.ClOSE:
            template = loader.get_template('poll_detail/close.html')
            poll_choices = []
            items = PollChoice.objects.filter(poll=poll)
            for item in items:
                choice = {"option":item.content, "users":[], "count":0}
                k = 0
                c =  UserPollChoice.objects.filter(poll=poll,choices=item)
                for i in c:
                    if i.get_full_name():
                        choice["users"].append(i.get_full_name())
                    else:
                        k =k + 1
                choice["count"] = len(choice["users"])
                if k >0:
                    choice["users"].append("Anonymous x"+str(k))
                    choice["count"] = k + len(choice["users"])-1
                poll_choices.append(choice)
                best_option = max(x['count'] for x in poll_choices)
            context = {
                'poll': poll,
                'choices':poll_choices,
                'best_option':best_option,
            }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))
        elif poll.state == StateChoices.OPENED:
            template = loader.get_template('poll_detail/opened.html')
            if request.user.is_authenticated:
                a = UserPollChoice.objects.filter(poll=poll,creator=request.user).all()
                mychoices = []
                for i in a:
                    for j in i.choices.all():
                        mychoices.append(j)
                context = {
                    'poll': poll,
                    'mychoices': mychoices
                }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            else:
                context = {
                    'poll': poll,
                }
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))

# Validator Email Function
# Check if the string argument is a valid email or not
# Return True if it a valid email format or return False if validation failed
def validateEmail(email):
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email( email )
        return True
    except ValidationError:
        return False

# Poll Submit Function
# Allows submitting choices for a Poll
def poll_submit(request):
    pk = request.POST['pk']
    poll = get_object_or_404(Poll, pk=pk)
    if request.user.is_authenticated:
        if UserPollChoice.objects.filter(poll=poll, creator=request.user).count() != 0:
            messages.warning(request, 'Please do not submit your poll choices again!')
            return redirect('poll_detail', pk=pk)
        if poll.multi_choices:
            user_poll_choice = UserPollChoice.objects.create(
                poll=poll,
                creator=request.user
            )
            choice_pks = request.POST.getlist('choices')
            if choice_pks ==[]:
                messages.warning(request, 'Your poll submission was unsuccessful !')
                return redirect('poll_detail', pk=pk)
            for choice_pk in choice_pks:
                choice = get_object_or_404(PollChoice, pk=choice_pk)
                user_poll_choice.choices.add(choice)
        else:
            choice_pk = request.POST['choice']
            if choice_pk ==[]:
                messages.warning(request, 'Your poll submission was unsuccessful !')
                return redirect('poll_detail', pk=pk)
            choice = get_object_or_404(PollChoice, pk=choice_pk)
            user_poll_choice = UserPollChoice.objects.create(
                poll=poll,
                creator=request.user
            )
            user_poll_choice.choices.add(choice)
        messages.success(request, 'Your poll submission was successful!')
        return redirect('poll_detail', pk=pk)

    if poll.multi_choices:
        choice_pks = request.POST.getlist('choices')
        if choice_pks==[]:
            messages.warning(request, 'Your poll submission was unsuccessful !')
            return redirect('poll_detail', pk=pk)
        email = request.POST['email']
        if not email:
            messages.warning(request, 'Please enter an email address!')
            return redirect('poll_detail', pk=pk)
        exist = UserPollChoice.objects.filter(email=email)
        if exist:
            messages.warning(request, 'Please do not submit your poll choices again!')
            return redirect('poll_detail', pk=pk)
        user_poll_choice = UserPollChoice.objects.create(
            poll=poll,
            email=email
            )
        for choice_pk in choice_pks:
            choice = get_object_or_404(PollChoice, pk=choice_pk)
            user_poll_choice.choices.add(choice)
    else:
        try:
            choice_pk = request.POST['choice']
            email = request.POST['email']
            if not email or not validateEmail(email):
                raise Exception
            exist = UserPollChoice.objects.filter(email=email)
            if exist:
                messages.warning(request, 'Please do not submit your poll choices again!')
                return redirect('poll_detail', pk=pk)
            choice = get_object_or_404(PollChoice, pk=choice_pk)
            user_poll_choice = UserPollChoice.objects.create(
                poll=poll,
                email=email)
            user_poll_choice.choices.add(choice)
        except:
            messages.warning(request, 'Your poll submission was unsuccessful !')
            return redirect('poll_detail', pk=pk)
    messages.success(request, 'Your poll submission was successful!')
    return redirect('poll_detail', pk=pk)


# Poll create Function
# if request.user.id ==> registred user
# else ==> anonymous user
def poll_new(request):
    if request.method == 'GET':
        template = loader.get_template('poll_new.html')
        context = {
            'privacy_choices': privacy_choices,
        }
        context.update(return_statistics())
        return HttpResponse(template.render(context, request))
    else:
        title = request.POST['title']
        description = request.POST['description']
        multi = request.POST.get('multi', None)
        if multi == 'on':
            is_multi_choice = True
        else:
            is_multi_choice = False
        choices = request.POST.getlist('choices')
        choices_list = [ c for c in choices]
        users = request.POST.getlist('users')
        users = list(filter(None, users))
        privacy = request.POST.get('privacy')
        invalid_users = []
        for user in users:
            username = User.objects.filter(username=user).first()
            if username is None:
                invalid_users.append(user)
        if len(invalid_users)!=0:
            template = loader.get_template('poll_new.html')
            context = {
                'privacy_choices': privacy_choices,
                'title':title,
                'choices':choices_list,
                'description':description,
                'invited_users':users

            }
            context.update(return_statistics())
            usrr = ''

            for usr in invalid_users:
                usrr+= usr + " , "
            messages.warning(request, "{} does not exist!".format(usrr))
            return HttpResponse(template.render(context, request))

        if  title.isspace()==True or (choices_list[0]=='' or choices_list[1]=='')  or description.isspace()==True or ("".join(choices or None).isspace() or "".join(choices or None)=='' ) :
            template = loader.get_template('poll_new.html')
            context = {
                'title':title,
                'privacy_choices': privacy_choices,
                'choices':choices_list,
                'description':description,

            }
            context.update(return_statistics())
            messages.warning(request, 'Poll creation unsuccessful, Please make sure that all required information was entered !')
            return HttpResponse(template.render(context, request))
        elif request.user.id:
            try:
                poll = Poll.objects.create(
                    title=title,
                    description=description,
                    multi_choices=is_multi_choice,
                    privacy=privacy,
                    creator=request.user
                )
                for choice_content in choices:
                    PollChoice.objects.create(
                        content=choice_content,
                        poll=poll
                    )
                if privacy == '0':
                    for username in users:
                        user = User.objects.filter(username=username).first()
                        if user is not None:
                            poll.invited_users.add(user)
                messages.success(request, 'Poll successfully created!')
                return redirect('poll_detail', pk=poll.pk)
            except:
                messages.success(request, 'Poll successfully created!')
                return redirect('poll_detail', pk=poll.pk)

        else:
            try:
                poll = Poll.objects.create(
                    title=title,
                    description=description,
                    multi_choices=is_multi_choice
                    )
                for choice_content in choices:
                    PollChoice.objects.create(
                        content=choice_content,
                        poll=poll
                        )
                messages.success(request, 'Poll successfully created!')
                return redirect('poll_detail', pk=poll.pk)
            except:
                messages.success(request, 'Poll update successful!')
                return redirect('poll_detail', pk=poll.pk)

# Poll update Funtion
# it allows to update a Poll if the user is his creator or is an admin
@login_required
def poll_update(request,pk):
    poll = get_object_or_404(Poll, pk=pk)
    if poll.state == StateChoices.ClOSE or(request.user == poll.creator or request.user.is_superuser )== False:
        messages.warning(request, 'Permission denied :/')
        return redirect('poll_detail', pk=pk)
    else:
        if request.method == 'GET':
            p = PollChoice.objects.filter(poll=poll)
            template = loader.get_template('poll_update.html')
            invited_users = [ c for c in poll.invited_users.all()]
            choices_list = [ c for c in p]
            context = {
                'privacy_choices': privacy_choices,
                'title':poll.title,
                'choices':choices_list,
                'description':poll.description,
                'invited_users':invited_users

            }
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))

        else:
            title = request.POST['title']
            description = request.POST['description']
            multi = request.POST.get('multi', None)
            if multi == 'on':
                is_multi_choice = True
            else:
                is_multi_choice = False
            choices = request.POST.getlist('choices')
            users = request.POST.getlist('users')
            privacy = request.POST.get('privacy')
            if  title.isspace()==True or description.isspace()==True or ("".join(choices or None).isspace() or "".join(choices or None)=='' ) :
                messages.warning(request, 'Poll update unsuccessful')
                return redirect('poll_detail', pk=pk)
            else:
                poll = Poll.objects.filter(pk=pk).update(
                            title=title,
                            description=description,
                            multi_choices=is_multi_choice,
                            privacy=privacy,
                        )

                poll = get_object_or_404(Poll, pk=pk)
                PollChoice.objects.filter(poll=poll).delete()
                for choice_content in choices:
                    PollChoice.objects.create(
                                content=choice_content,
                                poll=poll)

                poll.invited_users.clear()
                if privacy == '0':
                    for username in users:
                        user = User.objects.filter(username=username).first()
                        if user is not None:
                            poll.invited_users.add(user)
                        poll.invited_users.add(request.user)
                messages.success(request, 'Poll update successful')
                return redirect('poll_detail', pk=pk)


# Poll close Function
# Allows to close a Poll and send a notifications email for his participants
@login_required(login_url='/login/')
def poll_close(request, pk=None):
    poll = get_object_or_404(Poll, pk=pk)
    if (poll.state == StateChoices.ClOSE) or (request.user == poll.creator or request.user.is_superuser )== False:
        messages.warning(request, 'No permission !')
        return redirect('poll_detail', pk=pk)
    e = UserPollChoice.objects.filter(poll=poll)
    users = [x.creator.email for x in e if x.creator]
    users = users + [x.email for x in e if not x.creator]
    if users:
        for user in users:
            html_message = loader.render_to_string(
                'mail_template.html',
                {
                    'title':  poll.title,
                    'type': 'poll',
                    'link': f'http://127.0.0.1:8000/poll/{poll.pk}',
                })
            send_mail('Link Up Notification',poll.title,settings.DEFAULT_FROM_EMAIL,[user],fail_silently=True,html_message=html_message)

    poll.state = StateChoices.ClOSE
    poll.save()
    messages.success(request, 'Poll closed successfully!')
    return redirect('poll_detail', pk=poll.pk)

## OTHER FUNCTIONS ###

# Update User informations Function
# u_form ==> Name, Email fields
# p_form ==> Picture profile field
@login_required
def profile(request):
    if request.method == 'POST':
        u_form = userupdateform(request.POST, instance=request.user)
        p_form = profile_update_form(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, f'Your account has been updated!')
            return redirect ('profile')
    else:
        u_form = userupdateform(instance=request.user)
        p_form = profile_update_form(instance=request.user.profile)

    context = {
    'u_form': u_form,
    'p_form': p_form
    }
    return render(request, 'linkup/profile_update_form.html', context)

# Dashboard Page Function
@login_required(login_url='/login/')
def user_profile(request):
    template = loader.get_template('user_profile.html')
    scheduling_event = request.user.event_set.filter(state=StateChoices.OPENED)[:5]
    events_created = Event.objects.filter(creator=request.user)[:5]
    events_invitation = Event.objects.filter(invited_users__pk=request.user.pk)[:5]
    scheduled_event = request.user.event_set.filter(state=StateChoices.ClOSE)[:5]
    polls_created = Poll.objects.filter(creator=request.user)[:5]
    close_polls = request.user.poll_set.filter(state=StateChoices.ClOSE)[:5]
    opened_polls = request.user.poll_set.filter(state=StateChoices.OPENED)[:5]
    poll_invitation = Poll.objects.filter(invited_users__pk=request.user.pk)[:5]

    context = {
        'title':'Profile',
        'scheduling_event': scheduling_event,
        'events_created': events_created,
        'scheduled_event': scheduled_event,
        'events_invitation': events_invitation,
        'polls_created': polls_created,
        'close_polls': close_polls,
        'opened_polls': opened_polls,
        'poll_invitation': poll_invitation
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# Logout Function
@login_required(login_url='/login/')
def logout_deal(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    return redirect('index')

# Register Function
# With error handle infos
def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        template = loader.get_template('register.html')
        if request.method == 'POST':
            username = request.POST['username']
            user = User.objects.filter(username=username)
            if username is None or username == '' or user:
                if user:
                    messages.warning(request,"This username is already in use ! ")
                else:
                    messages.warning(request,"This username is invalid ! ")
                context = {}
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            email = request.POST['email']
            if email is None or email == '':
                messages.warning(request,"Email address is invalid ! ")
                context = {}
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            password = request.POST['password']
            if password is None or password == '':
                messages.warning(request,"Password is invalid ! ")
                context = {}
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            recaptcha_response = request.POST.get('g-recaptcha-response')
            url = 'https://www.google.com/recaptcha/api/siteverify'
            values = {
                'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                'response': recaptcha_response
            }
            data = urllib.parse.urlencode(values).encode()
            req =  urllib.request.Request(url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode())
            if result['success']:
                pass
            else:
                messages.warning(request,"reCAPTCHA  is invalid ! ")
                context = {}
                context.update(return_statistics())
                return HttpResponse(template.render(context, request))
            # Below line creates username
            User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
            messages.success(request, 'You have successfully registered ! '+'\n'+'Now you can Log In :)')
            return redirect('login')

        elif request.method == 'GET':
            template = loader.get_template('register.html')
            context = {}
            context.update(return_statistics())
            return HttpResponse(template.render(context, request))

# Login Function
def login_deal(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('/profile')
        else:
            messages.warning(request, 'Incorrect password or username ! ')
            return redirect('login')

    elif request.method == 'GET':
        template = loader.get_template('login.html')
        context = {}
        context.update(return_statistics())
        return HttpResponse(template.render(context, request))

# Show more query on dashboard sections
@login_required(login_url='/login/')
def more(request, query):
    if query == 'scheduled_events':
        queryset = request.user.event_set.filter(state=StateChoices.ClOSE)
        template = loader.get_template('event_list.html')
    elif query == 'scheduling_events':
        queryset = request.user.event_set.filter(state=StateChoices.OPENED)
        template = loader.get_template('event_list.html')
    elif query == 'events_invitation':
        queryset = Event.objects.filter(invited_users__pk=request.user.pk)
        template = loader.get_template('event_list.html')
    elif query == 'created_events':
        queryset = Event.objects.filter(creator=request.user)
        template = loader.get_template('event_list.html')
    elif query == 'poll_invitation':
        queryset = Poll.objects.filter(invited_users__pk=request.user.pk)
        template = loader.get_template('poll_list.html')
    elif query == 'close_polls':
        queryset = request.user.poll_set.filter(state=StateChoices.ClOSE)
        template = loader.get_template('poll_list.html')
    elif query == 'opened_polls':
        queryset = request.user.poll_set.filter(state=StateChoices.OPENED)
        template = loader.get_template('poll_list.html')
    elif query == 'polls_created':
        queryset = Poll.objects.filter(creator=request.user)
        template = loader.get_template('poll_list.html')
    paginator = Paginator(queryset, 10)
    page = request.GET.get('page')
    data = paginator.get_page(page)
    context = {
        'data': data,
        'title': 'Link Up Poll List'
    }
    context.update(return_statistics())
    return HttpResponse(template.render(context, request))

# Change Password Function
# Allows users to change their password, error handling also applied
@login_required(login_url='/login/')
def change_password(request):
    if request.method == 'POST':
        old_password = request.POST.get('oldPassword')
        user = authenticate(username=request.user.username, password=old_password)
        if user is None:
            messages.warning(request, 'All fields are required ! ')
            return redirect('change_password')
        new_password = request.POST.get('newPassword')
        new_password_repeat = request.POST.get('newPasswordRepeat')
        if (new_password.isspace=='' or new_password_repeat=='') or new_password!= new_password_repeat:
            messages.warning(request, 'Your new passwords did not match ! ')
            return redirect('change_password')
        else:
            request.user.set_password(new_password)
            request.user.save()
            messages.success(request, 'Your password has been changed successfully, You should re-login now !')
            return redirect('index')
    elif request.method == 'GET':
        template = loader.get_template('change_password.html')
        context = {}
        context.update(return_statistics())
        return HttpResponse(template.render(context, request))
