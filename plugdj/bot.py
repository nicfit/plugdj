import logging
from . import PlugDJ
from .events import from_json

log = logging.getLogger(__name__)


class Bot(PlugDJ):

    def __init__(self, email, password, room=None):
        self._current_room = None
        super().__init__(email, password, listener=self)
        if room:
            self.join_room(room)

    def __call__(self, event):
        e = from_json(event)
        log.debug("got an event, it was %r" % e)

        handler = f"_on{e.__class__.__name__}Event"
        if hasattr(self, handler):
            getattr(self, handler)(e)
        else:
            log.debug(f"Event {handler} method not defined")

    def join_room(self, room):
        r = super().join_room(room)
        self._current_room = self.room_state()["data"][0]
        self._onJoinRoom(room, self._current_room)
        return r

    @property
    def current_room(self):
        return self._current_room

    @property
    def current_tune(self):
        return self._current_room["playback"] \
                if self._current_room and "playback" in self.current_room \
                else None

    def _onJoinRoom(self, room, state):
        pass
