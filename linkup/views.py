from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import redirect, get_object_or_404, render
from django.template import loader
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.db.models import Q
from django.views.decorators.http import require_POST, require_http_methods
import requests as req
from .forms import RegistrationForm
import collections
from django.core.mail import send_mail
from django.template import loader
import json
from datetime import datetime
from .forms import  UserUpdateForm as userupdateform
from .forms import  ProfileUpdateForm as profile_update_form
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
def _integer_pk(value):
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise Http404
    if number < 1:
        raise Http404
    return number

def _can_access(request, item):
    user = request.user
    return item.privacy == PrivacyChoices.PUBLIC or (
        user.is_authenticated and (
            user.is_superuser or item.creator_id == user.pk
            or item.invited_users.filter(pk=user.pk).exists()
        )
    )

def _visible_to(queryset, user):
    if user.is_authenticated:
        if user.is_superuser:
            return queryset
        return queryset.filter(
            Q(privacy=PrivacyChoices.PUBLIC) | Q(creator=user) | Q(invited_users=user)
        ).distinct()
    return queryset.filter(privacy=PrivacyChoices.PUBLIC)

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
    delta = abs(datetime.strptime(d2.strip(), "%d/%m/%Y %H:%M") - datetime.strptime(d1.strip(), "%d/%m/%Y %H:%M"))
    hours, remainder = divmod(delta.seconds, 3600)
    minutes = remainder // 60
    parts = []
    if delta.days:
        parts.append(f"{delta.days} day{'s' if delta.days != 1 else ''}")
    if hours:
        parts.append(f"{hours}h")
    if minutes or not parts:
        parts.append(f"{minutes}m")
    return " ".join(parts)

# Event List Function
# Return Event list page with paginator to 10 per page
def event_list(request):
    events = _visible_to(Event.objects.all(), request.user)
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
    if not _can_access(request, event):
        raise PermissionDenied
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
    if not _can_access(request, event):
        raise PermissionDenied
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
                    choice = {'datetime_choices': str(i.datetime_choices.first().content) if i.datetime_choices.first() else '', 'location_choices': str(i.location_choices.first().content) if i.location_choices.first() else '', 'creator': i.creator.username}
                    choices_list.append(choice)
                ddd = [x['datetime_choices'] for x in choices_list]
                lll = [x['location_choices'] for x in choices_list]
                d = [item for item, count in collections.Counter(ddd).items() if count > 1]
                if len(d) != 0:
                    best_date = len([c for c in ddd if c ==[item for item, count in collections.Counter(ddd).items() if count > 1][0]])
                else:
                    best_date = 1 if ddd else 0
                l = [item for item, count in collections.Counter(lll).items() if count > 1]
                if len(l) != 0:
                    best_location = len([c for c in lll if c ==[item for item, count in collections.Counter(lll).items() if count > 1][0]])
                else:
                    best_location = 1 if lll else 0
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
                choice = {'datetime_choices': str(i.datetime_choices.first().content) if i.datetime_choices.first() else '', 'location_choices': str(i.location_choices.first().content) if i.location_choices.first() else '', 'creator': i.creator.username}
                choices_list.append(choice)
            ddd = [x['datetime_choices'] for x in choices_list]
            lll = [x['location_choices'] for x in choices_list]
            d = [item for item, count in collections.Counter(ddd).items() if count > 1]
            if len(d) != 0:
                best_date = len([c for c in ddd if c ==[item for item, count in collections.Counter(ddd).items() if count > 1][0]])
            else:
                best_date = 1 if ddd else 0
            l = [item for item, count in collections.Counter(lll).items() if count > 1]
            if len(l) != 0:
                best_location = len([c for c in lll if c ==[item for item, count in collections.Counter(lll).items() if count > 1][0]])
            else:
                best_location = 1 if lll else 0
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
@require_http_methods(["GET", "POST"])
def event_new(request):
    if request.method == "POST":
            valid = (
                request.POST.get("title", "").strip() and len(request.POST.get("title", "")) <= 250
                and request.POST.get("description", "").strip()
                and request.POST.get("category") in {str(v) for v, _ in event_category_choices}
                and request.POST.get("importance") in {str(v) for v, _ in event_importance_choices}
                and request.POST.get("privacy", "1") in {"0", "1"}
                and any(v.strip() for v in request.POST.getlist("ddd"))
                and any(v.strip() for v in request.POST.getlist("location"))
                and all(len(v) <= 255 for v in request.POST.getlist("ddd") + request.POST.getlist("location"))
            )
            if not valid:
                messages.warning(request, "Enter a title, description, category, importance, date and location.")
                return render(request, "event_new.html", {
                    **return_statistics(), "privacy_choices": privacy_choices,
                    "event_category_choices": event_category_choices, "event_importance_choices": event_importance_choices,
                })
            if request.POST.get("privacy") == "0" and not request.user.is_authenticated:
                raise PermissionDenied
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
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category = request.POST.get('category', None)
        importance = request.POST.get('importance', None)
        privacy = request.POST.get('privacy', '1')
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
        if not title or not description or (("".join(location_choices))=='') or (("".join(datetime_choices))==''):

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
    if not _can_access(request, event):
        raise PermissionDenied
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
            title = request.POST.get('title', '').strip()
            description = request.POST.get('description', '').strip()
            category = request.POST.get('category', None)
            importance = request.POST.get('importance', None)
            privacy = request.POST.get('privacy', '1')
            datetime_choices = request.POST.getlist('ddd')
            location_choices = request.POST.getlist('location')
            invited_users = request.POST.getlist('invited')
            if not title or not description or (("".join(location_choices))=='') or (("".join(datetime_choices))==''):
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
@require_POST
def event_close(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not _can_access(request, event):
        raise PermissionDenied
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
@login_required
@require_http_methods(["GET", "POST"])
def event_join(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not _can_access(request, event):
        raise PermissionDenied
    existing = UserEventChoice.objects.filter(event=event, creator=request.user).first()
    if request.method == "GET":
        context = {"event": event, **return_statistics()}
        if existing:
            date = existing.datetime_choices.first()
            location = existing.location_choices.first()
            context.update(date=date.content if date else "", location=location.content if location else "")
        return render(request, "event_detail/choices.html" if existing else "event_detail/join.html", context)
    if event.state != StateChoices.OPENED:
        raise PermissionDenied
    if existing:
        messages.warning(request, "You have already submitted choices for this event.")
        return redirect("event_detail", pk=pk)
    dates = request.POST.getlist("datetime")
    locations = request.POST.getlist("location")
    if not dates or not locations:
        messages.warning(request, "Select a date and location.")
        return redirect("event_join", pk=pk)
    date_choices = [get_object_or_404(DatetimeChoice, pk=_integer_pk(value), event=event) for value in dates]
    location_choices = [get_object_or_404(LocationChoice, pk=_integer_pk(value), event=event) for value in locations]
    with transaction.atomic():
        vote = UserEventChoice.objects.create(event=event, creator=request.user)
        vote.datetime_choices.set(date_choices)
        vote.location_choices.set(location_choices)
    messages.success(request, "Your event choices have been saved.")
    return redirect("event_detail", pk=pk)


# Event Submit Function
# Submission mechanismn
@login_required
@require_POST
def event_submit(request):
    event = get_object_or_404(Event, pk=_integer_pk(request.POST.get("pk")))
    if not _can_access(request, event) or event.state != StateChoices.OPENED:
        raise PermissionDenied
    if UserEventChoice.objects.filter(event=event, creator=request.user).exists():
        messages.warning(request, "You have already submitted choices for this event.")
        return redirect("event_detail", pk=event.pk)
    if not request.POST.get("choice") or not request.POST.get("choice2"):
        messages.warning(request, "Select a date and location.")
        return redirect("event_detail", pk=event.pk)
    date = get_object_or_404(DatetimeChoice, pk=_integer_pk(request.POST["choice"]), event=event)
    location = get_object_or_404(LocationChoice, pk=_integer_pk(request.POST["choice2"]), event=event)
    with transaction.atomic():
        vote = UserEventChoice.objects.create(event=event, creator=request.user)
        vote.datetime_choices.add(date)
        vote.location_choices.add(location)
    messages.success(request, "Your event choices have been saved.")
    return redirect("event_detail", pk=event.pk)

### POOL FUNCTIONS ###

# Poll List Function
# Return Poll list page with paginator to 10 per page
def poll_list(request):
    polls = _visible_to(Poll.objects.all(), request.user)
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
    if not _can_access(request, poll):
        raise PermissionDenied
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
    polls = _visible_to(Poll.objects.filter(privacy=PrivacyChoices.PRIVATE), request.user)
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
    if not _can_access(request, poll):
        raise PermissionDenied
    if poll.privacy == PrivacyChoices.PRIVATE:
        if (request.user in poll.invited_users.all()) or (request.user == poll.creator) or request.user.is_superuser:
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
                best_option = 0
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
            best_option = 0
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
@require_POST
def poll_submit(request):
    poll = get_object_or_404(Poll, pk=_integer_pk(request.POST.get("pk")))
    if not _can_access(request, poll) or poll.state != StateChoices.OPENED:
        raise PermissionDenied
    values = request.POST.getlist("choices") if poll.multi_choices else [request.POST.get("choice")]
    if not values or any(not value for value in values):
        messages.warning(request, "Select at least one choice.")
        return redirect("poll_detail", pk=poll.pk)
    choices = [get_object_or_404(PollChoice, pk=_integer_pk(value), poll=poll) for value in set(values)]
    if request.user.is_authenticated:
        identity = {"creator": request.user}
    else:
        email = request.POST.get("email", "").strip().lower()
        try:
            validate_email(email)
        except ValidationError:
            messages.warning(request, "Enter a valid email address.")
            return redirect("poll_detail", pk=poll.pk)
        identity = {"email": email}
    if UserPollChoice.objects.filter(poll=poll, **identity).exists():
        messages.warning(request, "You have already submitted choices for this poll.")
        return redirect("poll_detail", pk=poll.pk)
    with transaction.atomic():
        vote = UserPollChoice.objects.create(poll=poll, **identity)
        vote.choices.set(choices)
    messages.success(request, "Your poll choices have been saved.")
    return redirect("poll_detail", pk=poll.pk)


# Poll create Function
# if request.user.id ==> registred user
# else ==> anonymous user
@require_http_methods(["GET", "POST"])
def poll_new(request):
    if request.method == "POST":
            values = [v.strip() for v in request.POST.getlist("choices") if v.strip()]
            if (not request.POST.get("title", "").strip() or len(request.POST.get("title", "")) > 255
                    or not request.POST.get("description", "").strip() or len(values) < 2
                    or any(len(v) > 255 for v in values) or request.POST.get("privacy", "1") not in {"0", "1"}):
                messages.warning(request, "Enter a title, description and at least two choices.")
                return render(request, "poll_new.html", {**return_statistics(), "privacy_choices": privacy_choices})
            if request.POST.get("privacy") == "0" and not request.user.is_authenticated:
                raise PermissionDenied
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
        privacy = request.POST.get('privacy', '1')
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
    if not _can_access(request, poll):
        raise PermissionDenied
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
            privacy = request.POST.get('privacy', '1')
            if  not title or not description or ("".join(choices or None).isspace() or "".join(choices or None)=='' ) :
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
@require_POST
def poll_close(request, pk=None):
    poll = get_object_or_404(Poll, pk=pk)
    if not _can_access(request, poll):
        raise PermissionDenied
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
@require_POST
def logout_deal(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    return redirect('index')

# Register Function
# With error handle infos
@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect("index")
    context = return_statistics()
    if request.method == "GET":
        return render(request, "register.html", context)
    data = request.POST.copy()
    data["password1"] = request.POST.get("password", "")
    data["password2"] = request.POST.get("password", "")
    form = RegistrationForm(data)
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.warning(request, error)
        return render(request, "register.html", context)
    if settings.RECAPTCHA_ENABLED:
        try:
            response = req.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data={"secret": settings.GOOGLE_RECAPTCHA_SECRET_KEY,
                      "response": request.POST.get("g-recaptcha-response", "")},
                timeout=5,
            )
            response.raise_for_status()
            verified = response.json().get("success") is True
        except (req.RequestException, ValueError):
            verified = False
        if not verified:
            messages.warning(request, "Verification failed. Please try again.")
            return render(request, "register.html", context)
    form.save()
    messages.success(request, "Your account is ready. You can now log in.")
    return redirect("login")

# Login Function
def login_deal(request):
    if request.user.is_authenticated:
        return redirect('/')
    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('profile')
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
@login_required
@require_http_methods(["GET", "POST"])
def change_password(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, {
            "old_password": request.POST.get("oldPassword", ""),
            "new_password1": request.POST.get("newPassword", ""),
            "new_password2": request.POST.get("newPasswordRepeat", ""),
        })
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Your password has been changed.")
            return redirect("profile")
        for errors in form.errors.values():
            for error in errors:
                messages.warning(request, error)
    return render(request, "change_password.html", return_statistics())
