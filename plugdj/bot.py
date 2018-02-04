import logging
from time import sleep
from pprint import pprint
from . import PlugDJ
from .events import from_json, Advance, MalformedEvent, Vote

log = logging.getLogger(__name__)


class Bot(PlugDJ):
    FRIEND_IDS = set()

    def __init__(self, email, password, room=None):
        super().__init__(email, password, listener=self)

        self._current_room = None
        self._current_tune = None
        self._me = self.user_info()
        log.info(f"me: {self._me}")
        self._friends = self.get_friends()["data"]

        if room:
            self.join_room(room)

    def __call__(self, event):
        """Web socket event handler."""
        try:
            e = from_json(event)
            log.debug("got an event, it was %r" % e)
        except MalformedEvent as ex:
            log.warning(str(ex))
            return

        # Update state

        if isinstance(e, Vote):
            self._current_room["votes"][e.i] = e.v

        if isinstance(e, Advance):
            if self._current_tune is not None:
                self._onPerformance(self._current_room)

            self._current_room["booth"]["currentDJ"] = e.c
            self._current_room["booth"]["waitingDJs"] = e.d
            self._current_room["playback"]["historyID"] = e.h
            self._current_room["playback"]["media"] = e.m
            self._current_room["playback"]["playlistID"] = e.p
            self._current_room["playback"]["startTime"] = e.t

            self._current_tune = self._current_room["playback"]

        # Invoke handlers
        handler = f"_on{e.__class__.__name__}Event"
        if hasattr(self, handler):
            getattr(self, handler)(e)
        else:
            log.debug(f"Event {handler} method not defined")

    def room_state(self):
        r = super().room_state()
        self._current_room = r["data"][0]
        if self._current_room and "playback" in self.current_room:
            self._current_tune = self._current_room["playback"] or None
        else:
            self._current_tune = None
        return r

    def join_room(self, room):
        r = super().join_room(room)
        self.room_state()  # Update
        self._onJoinRoom(self._current_room)
        return r

    @property
    def current_room(self):
        return self._current_room

    @property
    def current_tune(self):
        return self._current_tune

    def _onJoinRoom(self, room):
        pass

    def isFriend(self, id):
        return (id in self.FRIEND_IDS or  # Explicit
                id in  [f["id"] for f in self._friends]  # Plug friends
        )
