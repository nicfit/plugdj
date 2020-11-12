import json
from plugdj.events import from_json, Advance


def test_AdvanceEvent():
    adv = from_json(json.loads(
        '{"a":"advance","p":{"c":16057928,"d":[],"h":"b9b31186-bdf6-4428-b243-8603cd3c3a64","m":{"author":"The Brian Jonestown Massacre","format":1,"image":"http://i.ytimg.com/vi/OipL9ToIDuU/default.jpg","cid":"OipL9ToIDuU","duration":221,"title":"Lets Pretend It\'s Summer","id":319982261},"p":9112779,"t":"2020-11-12 18:44:06.500598"},"s":"asylum-fm"}'
    ))
    assert isinstance(adv, Advance)
    assert adv.c == 16057928
    assert adv.d == []
    assert adv.h == "b9b31186-bdf6-4428-b243-8603cd3c3a64"
    assert adv.media == {"author": "The Brian Jonestown Massacre",
                         "format": 1,
                         "image": "http://i.ytimg.com/vi/OipL9ToIDuU/default.jpg",
                         "cid": "OipL9ToIDuU",
                         "duration": 221,
                         "title": "Lets Pretend It\'s Summer",
                         "id": 319982261}

    assert adv.p == 9112779
    assert adv.t == "2020-11-12 18:44:06.500598"
    assert adv.s == "asylum-fm"


def test_CycleEvent():
    cycle = from_json(json.loads(
        '{"a":"playlistCycle","p":9112779,"s":"dashboard"}'
    ))
    assert cycle.playlist == 9112779
    assert cycle.room == "dashboard"


def test_EarnEvent():
    earn = from_json(json.loads(
        '{"a":"earn","p":{"pp":186444,"xp":42345,"level":11},"s":"dashboard"}'
    ))
    assert earn.level == 11
    assert earn.xp == 42345
    assert earn.pp == 186444
