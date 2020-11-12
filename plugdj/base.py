import time
from urllib.parse import urljoin
from requests import Session
from ws4py.client.threadedclient import WebSocketClient
from .events import from_json
from .util import js_var, logger, ms_since_epoch, LoginError
import json


class PlugREST(object):
    rest_url_base = "https://plug.dj"

    def __init__(self):
        self._session = Session()
        # TODO: appropriate ua
        self._session.headers.update({"User-Agent": "plugAPI_3.2.1"})

    def _post(self, path, return_req=False, **kwargs):
        req = self._session.post(self.to_url(path), **kwargs)
        if return_req:
            return req
        req.raise_for_status()
        return req.json()

    def _get(self, path, return_req=False, **kwargs):
        req = self._session.get(self.to_url(path), **kwargs)
        if return_req:
            return req
        req.raise_for_status()
        return req.json()

    def _put(self, path, return_req=False, **kwargs):
        req = self._session.put(self.to_url(path), **kwargs)
        if return_req:
            return req
        req.raise_for_status()
        return req.json()

    def _delete(self, path, return_req=False, **kwargs):
        req = self._session.delete(self.to_url(path), **kwargs)
        if return_req:
            return req
        req.raise_for_status()
        return req.json()

    def _get_root(self):
        return self._session.get(urljoin(self.rest_url_base, "/"))

    @classmethod
    def to_url(cls, endpoint):
        return urljoin(cls.rest_url_base, "/_/" + endpoint)

    def login(self, email, password):
        # request root of site
        resp = self._get_root().text
        csrf = js_var("_csrf", resp)
        if csrf is None:
            raise LoginError(resp)

        json = {"csrf": csrf, "email": email, "password": password}
        return self._post("auth/login", json=json)

    # many of these have implicit preconditions. not really REST.

    def join_room(self, room):
        return self._post("rooms/join", json={"slug": room})

    def user_info(self, uid=None):
        return self._get("users/me" if uid is None
                                    else "users/{:d}".format(uid))

    def skip(self):
        return self._post("booth/skip/me")

    def moderate_skip(self, user_id, history_id):
        json={"userID": user_id, "historyID": history_id}
        return self._post("booth/skip", json=json)

    def room_state(self):
        """ assumes already connected to room."""
        return self._get("rooms/state")

    def chat_delete(self, msg_id):
        return self._delete("/chat/{msg_id}".format(**locals()))

    def room_history(self):
        return self._get("rooms/history")

    def moderate_add_dj(self, user_id):
        """ adds a dj to the waitlist (nee booth). """
        return self._post("booth/add", json={"id": user_id})

    def moderate_ban_user(self, user_id, reason, duration):
        """ does what the tin label indicates. cf. https://github.com/plugCubed/plugAPI/wiki/%5Bactions%5D%20moderateBanUser
        @reason: int; [1..5]
        @duration: string; 'h', 'd', 'f' = hour, day, 5ever
        """
        json = {"userID": user_id, "reason": reason, "duration": duration}
        return self._post("bans/add", json=json)

    def join_booth(self):
        """ possibly unsupported. cf. `PlugAPI.prototype.joinBooth`. """
        return self._post("booth")

    def leave_booth(self):
        """ possibly unsupported. cf. `PlugAPI.prototype.leaveBooth`. """
        return self._delete("booth")

    def moderate_move_dj(self, user_id, position):
        json = {"userID": user_id, "position": position}
        return self._post("booth/move", json=json)

    def moderate_mute_user(self, user_id, reason, duration):
        json = {"userID": user_id, "reason": reason, "duration": duration}
        return self._post("mutes", json=json)

    def moderate_set_role(self, user_id, role):
        json = {"userID": user_id, "roleID": role}
        return self._post("staff/update", json=json)

    def moderate_remove_dj(self, user_id):
        return self._delete("booth/remove/%s" % user_id)

    def moderate_unmod_user(self, user_id):
        return self._delete("staff/%s" % user_id)

    def moderate_unban(self, user_id):
        return self._delete("bans/%s" % user_id)

    def moderate_unmute(self, user_id):
        return self._delete("mutes/%s" % user_id)

    def activate_playlist(self, playlist_id):
        return self._put("playlists/%s/activate" % playlist_id)

    def add_song_to_playlist(self, playlist_id, media, append=True):
        json = {"media": [media], "append": append}
        return self._post("playlists/%s/media/insert" % playlist_id, json=json)

    def create_playlist(self, name):
        return self._post("playlists", json={"name": name})

    def delete_playlist(self, playlist_id):
        return self._delete("playlists/%s" % playlist_id)

    def rename_playlist(self, playlist_id, new_name):
        return self._put("playlists/%s/rename" % playlist_id,
                         json={"name": new_name})

    def delete_playlist_media(self, playlist_id, *ids):
        json = {"ids": list(ids)}
        return self._post("playlists/%s/media/delete" % playlist_id, json=json)

    def get_playlists(self):
        return self._get("playlists")

    def get_playlist_medias(self, playlist_id):
        return self._get("playlists/%s/media" % playlist_id)

    def shuffle_playlist(self, playlist_id):
        return self._put("playlists/%s/shuffle" % playlist_id)

    def move_media(self, playlist_id, before_media_id, *ids):
        json = {"ids": ids,
                "beforeID": before_media_id}
        return self._put("playlists/%s/media/move" % playlist_id, json=json)

    def moderate_cycle_booth(self, should_cycle):
        json = {"shouldCycle": bool(should_cycle)}
        return self._put("booth/cycle", json=json)

    def change_room_info(self, name, description, welcome_msg):
        json = {"name": name, "description": description, "welcome":
                welcome_msg}
        return self._post("rooms/update", json=json)

    def moderate_lock_wait_list(self, locked, clear):
        return self._put("booth/lock", json={"isLocked": bool(locked),
                                             "removeAllDJs": bool(clear)})

    def user_get_avatars(self):
        return self._get("store/inventory/avatars")

    def user_set_avatar(self, avatar_id):
        return self._put("users/avatar", json={"id": avatar_id})

    def user_set_status(self, status):
        """ possibly unsupported. cf. `PlugAPI.prototype.setStatus`.
        @status: integer.
        """
        return self._put("users/status", json={"status": status})

    def get_all_staff(self):
        return self._get("staff")

    def get_friends(self):
        return self._get("friends")

    def request_friend(self, user_id):
        return self._post("friends", json={"id": user_id})

    def delete_friend(self, user_id):
        return self._delete("friends/%d" % user_id)

    def get_invites(self):
        return self._get("friends/invites")

    def accept_friend_request(self, user_id):
        return self.request_friend(user_id)
        #return self._post("friends", json={"id": user_id})

    def reject_friend_request(self, user_id):
        return self._put("friends/ignore", json={"id": user_id})

    def meh(self, history_id):
        # so what happens when abs(direction) != 1?
        json = {"direction": -1, "historyID": history_id}
        return self._post("votes", json=json)

    def woot(self, history_id):
        json = {"direction": 1, "historyID": history_id}
        return self._post("votes", json=json)

    def grab(self, playlist_id, history_id):
        json = {"playlistID": playlist_id, "historyID": history_id}
        return self._post("grabs", json=json)

    def search_rooms(self, query, page=1, limit=50):
        return self._get("rooms", params={"page": page, "limit": limit,
                                          "q": query})

    def get_rooms(self, page=1, limit=50):
        return self._get("rooms", params={"page": page, "limit": limit})

    def get_favorites(self, page=1, limit=50):
        return self._get("rooms/favorites", params={"page": page,
                                                    "limit": limit})

    def unfavorite(self, room_id):
        return self._delete("rooms/favorites/{:d}".format(room_id))

    def favorite(self, room_id):
        return self._post("rooms/favorites", json={"id": room_id})


class SockBase(object):
    """ whose primary purpose is to receive pushes and send chats. """

    ws_endpoint = "wss://godj.plug.dj:443/socket"

    def _recv(self): raise NotImplemented

    def _send(self, m): raise NotImplemented

    def authenticate(self, tok):
        """ sends auth token. """
        logger.debug("PlugSock: sending auth: " + tok)
        self.send("auth", tok)
        return self

    def send_chat(self, msg):
        if len(msg) > 256:
            logger.warn("Room.send_chat: msg len > 256; plug will likely "
                        "truncate.")
        return self.send("chat", msg)

    def send(self, event_type, event_data):
        """ sends generic json packed in plug's format. """
        msg = self.pack_msg(event_type, event_data)
        self._send(json.dumps(msg))
        return self

    def recv(self):
        return (from_json(e) for e in json.loads(self._recv()))

    def recv_all(self):
        return list(self.recv())

    def pack_msg(self, ty, dat):
        return {"a": ty, "p": dat, "t": ms_since_epoch()}


class PlugSock(SockBase):
    """ default ws impl based on ws4py. spawns its own thread. """

    _recv = lambda self: self.socket.recv()
    _send = lambda self, m: self.socket.send(m)

    def __init__(self, auth, listener, **kwargs):

        class _ThreadedPlugSock(WebSocketClient):
            last_ping = None

            def opened(innerself):
                self.authenticate(self.auth)

            def received_message(innerself, msg):
                logger.debug("_ThreadedPlugSock: received %r" % msg.data)

                if msg.data == b"h":
                    innerself.last_ping = time.time()

                try:
                    msgs = json.loads(str(msg))
                except ValueError:
                    return  # not a plug message.

                if callable(self.listener):
                    for msg in msgs:
                        if msg is not None:
                            self.listener(msg)

            def closed(innerself, code, reason=None):
                msg = "_ThreadedPlugSock: closed: %r %r" % (code, reason)
                logger.debug(msg)

        self.auth = auth
        self.listener = listener
        self.socket = _ThreadedPlugSock(self.ws_endpoint)
        self.socket.connect()
