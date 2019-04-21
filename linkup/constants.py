# These are the options for events and polls as well as definition of state with strings and booleans

event_category_choices = (
    (0, 'meeting'),
    (1, 'appointment'),
    (2, 'social'),
    (3, 'networking'),
    (4, 'catchup'),
    (5, 'other')
)

event_importance_choices = (
    (0, 'very urgent'),
    (1, 'urgent'),
    (2, 'normal')
)

privacy_choices = (
    (0, 'private'),
    (1, 'public')
)

state_choices = (
    (0, 'close'),
    (1, 'opened')
)


class PrivacyChoices:
    PUBLIC = 1
    PRIVATE = 0


class StateChoices:
    ClOSE = 0
    OPENED = 1
