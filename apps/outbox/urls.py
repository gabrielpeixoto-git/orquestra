"""URL configuration for outbox app."""

from django.urls import path

from apps.outbox.views import (
    discard_dead_letter,
    list_dead_letters,
    list_outbox_messages,
    replay_dead_letter,
)

app_name = "outbox"

urlpatterns = [
    path("outbox/", list_outbox_messages, name="list-outbox"),
    path("dead-letters/", list_dead_letters, name="list-dead-letters"),
    path("dead-letters/replay/", replay_dead_letter, name="replay-dead-letter"),
    path("dead-letters/discard/", discard_dead_letter, name="discard-dead-letter"),
]
