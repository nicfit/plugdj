import logging
import threading
from time import sleep
from pprint import pprint
from . import PlugDJ
from .events import from_json, Advance, MalformedEvent, Vote

log = logging.getLogger(__name__)


class Bot(PlugDJ):
    OWNER_ID = None
    FRIEND_IDS = set()

    def __init__(self, email, password, room=None):
        super().__init__(email, password, listener=self)
        self._current_room = None
        self._current_tune = None
        self._active_playlist = None
        self._listeners = []

        # Prime caches
        self._me = self.user_info()["data"][0]
        log.debug(f"me: {self._me}")
        self.get_friends()
        self.get_playlists()

        if room:
            self.join_room(room)

    @property
    def identity(self):
        return self._me

    def get_owner(self):
        return self.user_info(self.OWNER_ID) if self.OWNER_ID else None

    def is_user_in_room(self, user_id: int):
        for u in self.current_room["users"]:
            if u["id"] == user_id:
                return True
        return False

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
        for listener in [self] + self._listeners:
            handler = f"_on{e.__class__.__name__}Event"
            if hasattr(listener, handler):
                try:
                    getattr(listener, handler)(e)
                except Exception as ex:
                    log.error(f"Error in event callback {listener}.{handler}",
                              exc_info=ex)
            else:
                log.debug(f"Event {handler} method not defined for listener: "
                          f"{listener}")

    def get_friends(self):
        r = super().get_friends()
        self._friends = r["data"]
        return r

    def get_friend(self, friend_id):
        for f in self.get_friends()["data"]:
            if f["id"] == friend_id:
                return f
        return None

    def is_friend(self, id):
        return (id in self.FRIEND_IDS or  # Explicit
                id in  [f["id"] for f in self._friends]  # Plug friends
               )

    def get_playlists(self):
        r = super().get_playlists()
        self._playlists = {}
        for pl in r["data"]:
            self._playlists[pl["id"]] = pl
            self._playlists[pl["name"]] = pl
            if pl["active"]:
                self._active_playlist = pl["id"]
        return r

    def get_playlist(self, name):
        """Get a playlist. `name` may be a string name or int ID."""
        if name in self._playlists:
            return self._playlists[name]
        else:
            try:
                return self._playlists[int(name)]
            except:
                pass
            return None

    def create_playlist(self, name):
        r = super().create_playlist(name)
        self.get_playlists()
        return r

    def delete_playlist(self, playlist_id):
        r = super().delete_playlist(playlist_id)
        self.get_playlists()
        return r

    def activate_playlist(self, plid):
        r = super().activate_playlist(plid)
        self._active_playlist = plid
        for pl in self.playlists:
            pl["active"] = bool(pl["id"] == self._active_playlist)
        return r

    def grab(self, playlist_id, history_id):
        r = super().grab(playlist_id, history_id)
        self.get_playlists()
        return r

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

    def add_listener(self, listener):
        if listener not in self._listeners:
            self._listeners.append(listener)

    def remove_listener(self, listener):
        if listener in self._listeners:
            self._listeners.remove(listener)

    @property
    def current_room(self):
        return self._current_room

    @property
    def current_tune(self):
        return self._current_tune

    @property
    def current_dj(self):
        return self._current_room["booth"]["currentDJ"]

    @property
    def friends(self):
        return self._friends

    @property
    def playlists(self):
        return list({v['id']: v for v in self._playlists.values()}.values())

    def _onJoinRoom(self, room_json):
        log.debug(f"_onJoinRoom: {room_json}")

    def _sched(self, secs, func, args=None, kwargs=None):
        t = threading.Timer(secs, func, args or [], kwargs or {})
        t.start()
        return t
