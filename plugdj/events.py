from .util import MalformedEvent


def from_json(js):
    EventClass = event_map.get(js.get("a"))
    return EventClass(js) if EventClass is not None else UnknownEvent(js)


# because namedtuple is too restrictive; ignore extras
class PlugEvent(object):
    __slots__ = ()

    def __init__(self, json):
        for attr in self.__slots__:
            try:
                p = json["p"]
                # Certain events (e.g. friendRequest) have non-dict p values...
                setattr(self, attr, p[attr] if hasattr(p, "__getitem__") else p)
            except KeyError as ex:
                from six import  raise_from
                msg = "malformed event: " + repr(json)
                raise_from(MalformedEvent(msg), ex)


class AuthAck(PlugEvent):
    __slots__ = ("ack",)
    def __init__(self, json):
        self.ack = json["p"]

class Chat(PlugEvent):
    __slots__ = ("cid", "message", "uid", "un")

class Vote(PlugEvent):
    __slots__ = ("i", "v")

class Advance(PlugEvent):
    __slots__ = ("c", "d", "h", "m", "p", "t")

class UserJoin(PlugEvent):
    __slots__ = ("user", "room_slug")
    def __init__(self, json):
        self.user = json["p"]
        self.room_slug = json["s"]

class UserLeave(PlugEvent):
    __slots__ = ("user_id", "room_slug")
    def __init__(self, json):
        self.user_id = json["p"]
        self.room_slug = json["s"]


class FriendRequest(PlugEvent):
    __slots__ = ("p")


class Skip(PlugEvent):
    __slots__ = ("uid")


class UnknownEvent(PlugEvent):
    __slots__ = ("json",)
    def __init__(self, json):
        self.json = json

event_map = {
    "ack": AuthAck,
    "advance": Advance,
    "chat": Chat,
    "friendRequest": FriendRequest,
    "userJoin": UserJoin,
    "userLeave": UserLeave,
    "vote": Vote,
    "skip": Skip,
}

"""
    ADVANCE: 'advance',
    BAN: 'ban',
    BOOTH_LOCKED: 'boothLocked',
    CHAT: 'chat',
    CHAT_COMMAND: 'command',
    CHAT_DELETE: 'chatDelete',
    CHAT_LEVEL_UPDATE: 'roomMinChatLevelUpdate',
    COMMAND: 'command',
    DJ_LIST_CYCLE: 'djListCycle',
    DJ_LIST_UPDATE: 'djListUpdate',
    DJ_LIST_LOCKED: 'djListLocked',
    EARN: 'earn',
    FOLLOW_JOIN: 'followJoin',
    FLOOD_CHAT: 'floodChat',
    GRAB: 'grab',
    KILL_SESSION: 'killSession',
    MODERATE_ADD_DJ: 'modAddDJ',
    MODERATE_ADD_WAITLIST: 'modAddWaitList',
    MODERATE_AMBASSADOR: 'modAmbassador',
    MODERATE_BAN: 'modBan',
    MODERATE_MOVE_DJ: 'modMoveDJ',
    MODERATE_MUTE: 'modMute',
    MODERATE_REMOVE_DJ: 'modRemoveDJ',
    MODERATE_REMOVE_WAITLIST: 'modRemoveWaitList',
    MODERATE_SKIP: 'modSkip',
    MODERATE_STAFF: 'modStaff',
    NOTIFY: 'notify',
    PDJ_MESSAGE: 'pdjMessage',
    PDJ_UPDATE: 'pdjUpdate',
    PING: 'ping',
    PLAYLIST_CYCLE: 'playlistCycle',
    REQUEST_DURATION: 'requestDuration',
    REQUEST_DURATION_RETRY: 'requestDurationRetry',
    ROOM_CHANGE: 'roomChanged',
    ROOM_DESCRIPTION_UPDATE: 'roomDescriptionUpdate',
    ROOM_JOIN: 'roomJoin',
    ROOM_NAME_UPDATE: 'roomNameUpdate',
    ROOM_VOTE_SKIP: 'roomVoteSkip',
    ROOM_WELCOME_UPDATE: 'roomWelcomeUpdate',
    SESSION_CLOSE: 'sessionClose',
    SKIP: 'skip',
    STROBE_TOGGLE: 'strobeToggle',
    USER_COUNTER_UPDATE: 'userCounterUpdate',
    USER_FOLLOW: 'userFollow',
    USER_JOIN: 'userJoin',
    USER_LEAVE: 'userLeave',
    USER_UPDATE: 'userUpdate',
    VOTE: 'vote'
"""
