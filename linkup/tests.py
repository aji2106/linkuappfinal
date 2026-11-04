"""Regression coverage for the supported Django runtime and core workflows."""
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

import requests
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.loader import get_template
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from .forms import RegistrationForm
from .models import (
    DatetimeChoice, Event, LocationChoice, Poll, PollChoice,
    Profile, UserEventChoice, UserPollChoice,
)
from .views import period


class AppTestCase(TestCase):
    def setUp(self):
        self.media = TemporaryDirectory()
        self.addCleanup(self.media.cleanup)
        self.media_settings = override_settings(MEDIA_ROOT=self.media.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.owner = User.objects.create_user("owner", "owner@example.com", "test-Password-8346!")
        self.other = User.objects.create_user("other", "other@example.com", "test-Password-8346!")

    def poll(self, **kwargs):
        return Poll.objects.create(
            title=kwargs.pop("title", "A public poll"), description="Choose a time",
            multi_choices=kwargs.pop("multi_choices", False), creator=self.owner, **kwargs,
        )

    def event(self, **kwargs):
        return Event.objects.create(
            title=kwargs.pop("title", "A public event"), description="Meet up",
            category=0, importance=2, creator=self.owner, **kwargs,
        )


class TemplateTests(SimpleTestCase):
    def test_every_project_template_compiles(self):
        base = settings.BASE_DIR / "linkup" / "templates"
        for path in base.rglob("*.html"):
            with self.subTest(template=path.name):
                get_template(path.relative_to(base).as_posix())

    def test_duration_handles_minutes_and_crossing_midnight(self):
        self.assertEqual(period("04/11/2026 09:00", "04/11/2026 09:30"), "30m")
        self.assertEqual(period("04/11/2026 23:30", "05/11/2026 01:00"), "1h 30m")
        self.assertEqual(period("04/11/2026 09:00", "05/11/2026 10:15"), "1 day 1h 15m")


class AccountTests(AppTestCase):
    def test_user_creation_works_without_a_default_image_file(self):
        self.assertTrue(Profile.objects.filter(user=self.owner).exists())
        self.owner.first_name = "Updated"
        self.owner.save()
        self.assertEqual(Profile.objects.filter(user=self.owner).count(), 1)


    def test_uploaded_profile_image_is_resized(self):
        content = BytesIO()
        Image.new("RGB", (800, 600)).save(content, format="PNG")
        profile = self.owner.profile
        profile.image = SimpleUploadedFile("avatar.png", content.getvalue(), content_type="image/png")
        profile.save()
        with Image.open(profile.image.path) as image:
            self.assertLessEqual(max(image.size), 300)

    def test_public_pages_render_on_django_52(self):
        for name in ("index", "about", "login", "register", "event_list", "poll_list", "poll_list_private", "password_reset"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_login_and_profile(self):
        response = self.client.post(reverse("login"), {"username": "owner", "password": "test-Password-8346!"})
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(self.client.get(reverse("update")).status_code, 200)

    def test_profile_requires_login(self):
        self.assertRedirects(self.client.get(reverse("profile")), reverse("login") + "?next=/profile/")

    def test_login_form_contains_csrf_token(self):
        self.assertContains(self.client.get(reverse("login")), 'name="csrfmiddlewaretoken"')

    def test_registration_validates_passwords(self):
        response = self.client.post(reverse("register"), {"username": "newuser", "email": "new@example.com", "password": "123"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_registration_validates_email_and_missing_fields(self):
        for data in ({}, {"username": "newuser", "email": "not-an-email", "password": "GoodPassword-124897!"}):
            response = self.client.post(reverse("register"), data)
            self.assertEqual(response.status_code, 200)
            self.assertFalse(User.objects.filter(username="newuser").exists())

    def test_registration_creates_account_and_profile(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com", "password": "GoodPassword-124897!",
        })
        self.assertRedirects(response, reverse("login"))
        user = User.objects.get(username="newuser")
        self.assertTrue(user.check_password("GoodPassword-124897!"))
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_duplicate_email_is_rejected_case_insensitively(self):
        form = RegistrationForm({
            "username": "newuser", "email": "OWNER@example.com",
            "password1": "GoodPassword-124897!", "password2": "GoodPassword-124897!",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    @override_settings(RECAPTCHA_ENABLED=True)
    @patch("linkup.views.req.post", side_effect=requests.Timeout)
    def test_captcha_network_error_does_not_create_user(self, post):
        response = self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com", "password": "GoodPassword-124897!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="newuser").exists())
        self.assertEqual(post.call_args.kwargs["timeout"], 5)

    @override_settings(RECAPTCHA_ENABLED=True)
    @patch("linkup.views.req.post")
    def test_captcha_rejection_does_not_create_user(self, post):
        post.return_value = Mock(**{"json.return_value": {"success": False}})
        self.client.post(reverse("register"), {
            "username": "newuser", "email": "new@example.com", "password": "GoodPassword-124897!",
        })
        self.assertFalse(User.objects.filter(username="newuser").exists())




class PrivacyTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.private_poll = self.poll(title="Confidential poll title", privacy=0)
        PollChoice.objects.create(poll=self.private_poll, content="Yes")
        self.private_event = self.event(title="Confidential event title", privacy=0)

    def test_public_lists_hide_private_items(self):
        for name, title in (("poll_list", self.private_poll.title), ("poll_list_private", self.private_poll.title), ("event_list", self.private_event.title)):
            self.assertNotContains(self.client.get(reverse(name)), title)

    def test_non_invited_account_cannot_see_private_details_or_results(self):
        self.client.force_login(self.other)
        for name, item in (("poll_detail", self.private_poll), ("result_poll", self.private_poll), ("event_detail", self.private_event), ("result", self.private_event), ("event_join", self.private_event)):
            with self.subTest(route=name):
                self.assertEqual(self.client.get(reverse(name, args=[item.pk])).status_code, 403)

    def test_anonymous_cannot_see_private_results(self):
        for name, item in (("result_poll", self.private_poll), ("result", self.private_event)):
            self.assertEqual(self.client.get(reverse(name, args=[item.pk])).status_code, 403)

    def test_invited_account_can_see_private_items(self):
        self.private_poll.invited_users.add(self.other)
        self.private_event.invited_users.add(self.other)
        self.client.force_login(self.other)
        for name, item in (("poll_detail", self.private_poll), ("event_detail", self.private_event)):
            self.assertEqual(self.client.get(reverse(name, args=[item.pk])).status_code, 200)
        self.assertContains(self.client.get(reverse("poll_list_private")), self.private_poll.title)

    def test_owner_can_see_private_items(self):
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("poll_detail", args=[self.private_poll.pk])).status_code, 200)
        self.assertEqual(self.client.get(reverse("event_detail", args=[self.private_event.pk])).status_code, 200)

    def test_closed_empty_poll_renders(self):
        self.private_poll.state = 0
        self.private_poll.save()
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse("poll_detail", args=[self.private_poll.pk])).status_code, 200)


class VotingTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.first_poll = self.poll()
        self.second_poll = self.poll(title="Second poll")
        self.choice = PollChoice.objects.create(poll=self.first_poll, content="Tuesday")
        self.other_choice = PollChoice.objects.create(poll=self.second_poll, content="Wednesday")
        self.first_event = self.event()
        self.second_event = self.event(title="Second event")
        self.date = DatetimeChoice.objects.create(event=self.first_event, content="04/11/2026 09:00 - 04/11/2026 10:00")
        self.location = LocationChoice.objects.create(event=self.first_event, content="London")
        self.other_date = DatetimeChoice.objects.create(event=self.second_event, content="Another date")

    def test_logged_in_poll_vote_is_saved_once(self):
        self.client.force_login(self.other)
        data = {"pk": self.first_poll.pk, "choice": self.choice.pk}
        self.assertEqual(self.client.post(reverse("poll_submit"), data).status_code, 302)
        self.client.post(reverse("poll_submit"), data)
        vote = UserPollChoice.objects.get(poll=self.first_poll, creator=self.other)
        self.assertEqual(list(vote.choices.all()), [self.choice])

    def test_anonymous_can_vote_in_two_different_polls(self):
        for poll, choice in ((self.first_poll, self.choice), (self.second_poll, self.other_choice)):
            self.client.post(reverse("poll_submit"), {"pk": poll.pk, "choice": choice.pk, "email": "voter@example.com"})
        self.assertEqual(UserPollChoice.objects.filter(email="voter@example.com").count(), 2)

    def test_anonymous_duplicate_vote_in_same_poll_is_blocked(self):
        data = {"pk": self.first_poll.pk, "choice": self.choice.pk, "email": "voter@example.com"}
        self.client.post(reverse("poll_submit"), data)
        self.client.post(reverse("poll_submit"), data)
        self.assertEqual(UserPollChoice.objects.filter(poll=self.first_poll).count(), 1)

    def test_cross_poll_choices_are_rejected(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("poll_submit"), {"pk": self.first_poll.pk, "choice": self.other_choice.pk})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(UserPollChoice.objects.exists())

    def test_empty_multi_choice_does_not_create_partial_vote(self):
        self.first_poll.multi_choices = True
        self.first_poll.save()
        self.client.force_login(self.other)
        self.client.post(reverse("poll_submit"), {"pk": self.first_poll.pk})
        self.assertFalse(UserPollChoice.objects.exists())

    def test_invalid_anonymous_email_is_rejected(self):
        self.client.post(reverse("poll_submit"), {"pk": self.first_poll.pk, "choice": self.choice.pk, "email": "invalid"})
        self.assertFalse(UserPollChoice.objects.exists())

    def test_closed_poll_rejects_votes(self):
        self.first_poll.state = 0
        self.first_poll.save()
        self.assertEqual(self.client.post(reverse("poll_submit"), {"pk": self.first_poll.pk, "choice": self.choice.pk, "email": "voter@example.com"}).status_code, 403)
        self.assertFalse(UserPollChoice.objects.exists())

    def test_private_poll_rejects_uninvited_vote(self):
        self.first_poll.privacy = 0
        self.first_poll.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("poll_submit"), {"pk": self.first_poll.pk, "choice": self.choice.pk}).status_code, 403)

    def test_event_vote_is_saved_once(self):
        self.client.force_login(self.other)
        data = {"pk": self.first_event.pk, "choice": self.date.pk, "choice2": self.location.pk}
        self.client.post(reverse("event_submit"), data)
        self.client.post(reverse("event_submit"), data)
        vote = UserEventChoice.objects.get(event=self.first_event, creator=self.other)
        self.assertEqual(list(vote.datetime_choices.all()), [self.date])
        self.assertEqual(list(vote.location_choices.all()), [self.location])

    def test_cross_event_choice_does_not_create_vote(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("event_submit"), {"pk": self.first_event.pk, "choice": self.other_date.pk, "choice2": self.location.pk})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(UserEventChoice.objects.exists())

    def test_event_join_validates_all_choices_before_saving(self):
        self.client.force_login(self.other)
        response = self.client.post(reverse("event_join", args=[self.first_event.pk]), {"datetime": [self.other_date.pk], "location": [self.location.pk]})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(UserEventChoice.objects.exists())

    def test_closed_event_rejects_votes(self):
        self.first_event.state = 0
        self.first_event.save()
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(reverse("event_submit"), {"pk": self.first_event.pk, "choice": self.date.pk, "choice2": self.location.pk}).status_code, 403)

    def test_vote_endpoints_require_post_and_handle_bad_ids(self):
        self.client.force_login(self.other)
        for name in ("event_submit", "poll_submit"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 405)
            for bad in ("nonsense", "", "-1"):
                self.assertEqual(self.client.post(reverse(name), {"pk": bad}).status_code, 404)

    def test_closing_and_logout_require_post(self):
        self.client.force_login(self.owner)
        for name, args in (("event_close", [self.first_event.pk]), ("poll_close", [self.first_poll.pk]), ("logout", [])):
            self.assertEqual(self.client.get(reverse(name, args=args)).status_code, 405)

    def test_owner_can_close_poll_and_event(self):
        self.client.force_login(self.owner)
        for name, item in (("event_close", self.first_event), ("poll_close", self.first_poll)):
            self.assertEqual(self.client.post(reverse(name, args=[item.pk])).status_code, 302)
            item.refresh_from_db()
            self.assertEqual(item.state, 0)

    def test_close_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(reverse("event_close", args=[self.first_event.pk])).status_code, 403)
        self.first_event.refresh_from_db()
        self.assertEqual(self.first_event.state, 1)


class CreationTests(AppTestCase):
    def test_creation_pages_render(self):
        for name in ("event_new", "poll_new"):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200)

    def test_incomplete_creations_are_validation_errors(self):
        for name in ("event_new", "poll_new"):
            self.assertEqual(self.client.post(reverse(name), {}).status_code, 200)
        self.assertFalse(Event.objects.exists())
        self.assertFalse(Poll.objects.exists())

    def test_create_public_poll(self):
        data = {"title": "New poll", "description": "Pick one", "privacy": "1", "choices": ["A", "B"]}
        response = self.client.post(reverse("poll_new"), data)
        self.assertEqual(response.status_code, 302)
        poll = Poll.objects.get(title="New poll")
        self.assertEqual(poll.pollchoice_set.count(), 2)
        self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_create_public_event(self):
        response = self.client.post(reverse("event_new"), {
            "title": "New event", "description": "Meet up", "privacy": "1",
            "category": "0", "importance": "2", "ddd": ["04/11/2026 09:00 - 04/11/2026 10:00"], "location": ["London"],
        })
        self.assertEqual(response.status_code, 302)
        event = Event.objects.get(title="New event")
        self.assertEqual(event.datetime_choices.count(), 1)
        self.assertEqual(event.location_choices.count(), 1)
        self.assertEqual(self.client.get(response.url).status_code, 200)

    def test_private_creation_requires_a_signed_in_owner(self):
        poll_data = {"title": "Private poll", "description": "Pick one", "privacy": "0", "choices": ["A", "B"]}
        self.assertEqual(self.client.post(reverse("poll_new"), poll_data).status_code, 403)
        self.client.force_login(self.owner)
        response = self.client.post(reverse("poll_new"), poll_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Poll.objects.get(title="Private poll").creator, self.owner)

    def test_owner_can_open_update_forms(self):
        self.client.force_login(self.owner)
        poll = self.poll()
        PollChoice.objects.create(poll=poll, content="A")
        event = self.event()
        for name, item in (("event_update", event), ("poll_update", poll)):
            self.assertEqual(self.client.get(reverse(name, args=[item.pk])).status_code, 200)

    def test_bundled_default_avatars_do_not_depend_on_uploads(self):
        self.assertEqual(self.owner.profile.image_url, "/static/linkup/default-profile.png")

    def test_password_reset_prepares_email_with_current_django(self):
        from django.core import mail
        response = self.client.post(reverse("password_reset"), {"email": self.owner.email})
        self.assertRedirects(response, reverse("password_reset_done"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("password-reset-confirm", mail.outbox[0].body)

class PasswordChangeTests(AppTestCase):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.owner)

    def test_password_change_preserves_session(self):
        response = self.client.post(reverse("change_password"), {
            "oldPassword": "test-Password-8346!",
            "newPassword": "DifferentPassword-739246!",
            "newPasswordRepeat": "DifferentPassword-739246!",
        })
        self.assertRedirects(response, reverse("profile"))
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("DifferentPassword-739246!"))
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)

    def test_weak_new_password_is_rejected(self):
        self.client.post(reverse("change_password"), {
            "oldPassword": "test-Password-8346!", "newPassword": "123", "newPasswordRepeat": "123",
        })
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("test-Password-8346!"))

    def test_mismatched_or_missing_password_is_rejected(self):
        for data in ({}, {"oldPassword": "test-Password-8346!", "newPassword": "DifferentPassword-739246!", "newPasswordRepeat": "different"}):
            self.assertEqual(self.client.post(reverse("change_password"), data).status_code, 200)
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("test-Password-8346!"))

    def test_wrong_old_password_is_rejected(self):
        self.client.post(reverse("change_password"), {
            "oldPassword": "wrong", "newPassword": "DifferentPassword-739246!", "newPasswordRepeat": "DifferentPassword-739246!",
        })
        self.owner.refresh_from_db()
        self.assertTrue(self.owner.check_password("test-Password-8346!"))
