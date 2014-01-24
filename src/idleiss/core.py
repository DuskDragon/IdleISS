from math import log

from .user import User
from .event import GameEngineEvent


class TimeOutofBounds(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)


class GameEngine(object):

    def __init__(self):
        self.users = {}

        # The current world_timestamp - only updated whenever the world
        # is updated by calling update_world with the current/latest
        # simulated timestamp.
        self.world_timestamp = 0

        # this should be a dequeue and must be thread safe.
        self._engine_events = []

    def add_event(self, event_type, **kw):
        if 'timestamp' in kw:
            # this is a bit of a magic as we assume that any keyword
            # arguments that are called `timestamp` relates to the
            # current time.  We check that the engine hasn't processed
            # any timestamp future to this.  If it is, force it to where
            # the engine last checked.
            kw['timestamp'] = max(kw['timestamp'], self.world_timestamp)

        self._engine_events.append(GameEngineEvent(event_type, **kw))

    def get_user(self, user_id):
        if user_id not in self.users:
            raise ValueError
        return self.users[user_id]

    def user_logged_in(self, user_id, timestamp):
        if user_id not in self.users:
            # create a user if that user_id is never seen before.
            self.users[user_id] = User(user_id)

        user = self.get_user(user_id)
        self.add_event(user.log_in, timestamp=timestamp)

    # Honestly I'm not even sure if I want to penalize messages ... hmmm
    #def user_room_message(self, user_id, message, timestamp):
        #however penalties are not yet implemented
    #    if user_id not in self.users:
    #        raise ValueError

    #    self.users[user_id].last_active = timestamp

    def user_logged_out(self, user_id, timestamp):
        user = self.get_user(user_id)
        self.add_event(user.log_out, timestamp=timestamp)

    def update_world(self, timestamp):
        if timestamp == self.world_timestamp:
            return []
        if timestamp < self.world_timestamp:
            # can't go back in time for now.
            raise TimeOutofBounds("already processed this timestamp")

        time_diff = timestamp - self.world_timestamp

        event_results = []

        # give the _engine_events a fresh start and grab everything that
        # has happened so far that needed our immediate attention.
        # XXX this is also probably not thread safe...  we fix this later.
        self._engine_events, engine_events = [], self._engine_events
        for engine_event in engine_events:
            event_results.append(engine_event())

        #### Pay Resources and Update total_idle_time
        for user_id in self.users:
            user = self.get_user(user_id)
            if not user.online:
                # skip offline users.
                continue

            user.update(timestamp)

            #### Random Events
            #### Calculate Battles
            #### Produce Units
            #### Other Events?

        self.world_timestamp = timestamp
        return event_results
