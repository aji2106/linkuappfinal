from django.contrib import admin

from linkup.models import Event, Poll, PollChoice, DatetimeChoice,\
					LocationChoice, Profile


# Register your models here.


class DatetimeInline(admin.TabularInline):
	model = DatetimeChoice


class LocationInline(admin.TabularInline):
   	 model = LocationChoice


class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'importance', 'category')
    inlines = [DatetimeInline, LocationInline]


class PollChoiceInline(admin.TabularInline):
    model = PollChoice


class PollAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'multi_choices')
    inlines = [PollChoiceInline]


admin.site.register(Event, EventAdmin)
admin.site.register(Profile)
admin.site.register(Poll, PollAdmin)
