import django.dispatch

post_save_children = django.dispatch.Signal(providing_args=['instance'])
