from django.apps import AppConfig


class LinkupConfig(AppConfig):
    name = 'linkup'

    def ready(self):
    	import linkup.signals
