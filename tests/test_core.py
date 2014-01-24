from unittest import TestCase

from idleiss import core


class CoreTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_base_game(self):
        engine = core.GameEngine()
        self.assertTrue(engine)

    def test_no_such_user(self):
        engine = core.GameEngine()
        self.assertRaises(ValueError, engine.get_user, 'an_user')

    # def test_user_interaction(self):
        # engine = core.GameEngine()
        # engine.user_logged_in('an_user', timestamp=1000)
        # engine.user_room_message('an_user', 'some_message', timestamp=1006)
        # idleness = engine.get_user_current_idleduration('an_user', timestamp=1010)
        # self.assertEqual(idleness, 4)

    def test_events_basic(self):
        engine = core.GameEngine()
        engine.user_logged_in('an_user', timestamp=1000)
        engine.users['an_user'].resources.basic_materials_income = 1
        engine.users['an_user'].resources.advanced_materials_income = 1
        engine.users['an_user'].resources.money_income = 1
        engine.update_world(timestamp=1007)

        self.assertEqual(engine.users['an_user'].resources.basic_materials, 7)
        self.assertEqual(engine.users['an_user'].resources.advanced_materials, 7)
        self.assertEqual(engine.users['an_user'].resources.money, 7)

        # can't trigger the same events again I guess?
        engine.update_world(timestamp=1007)

        self.assertEqual(engine.users['an_user'].resources.basic_materials, 7)
        self.assertEqual(engine.users['an_user'].resources.advanced_materials, 7)
        self.assertEqual(engine.users['an_user'].resources.money, 7)

        engine.update_world(timestamp=1008)


        self.assertEqual(engine.users['an_user'].resources.basic_materials, 8)
        self.assertEqual(engine.users['an_user'].resources.advanced_materials, 8)
        self.assertEqual(engine.users['an_user'].resources.money, 8)

    def test_events_skip_time(self):
        engine = core.GameEngine()
        engine.user_logged_in('an_user', timestamp=1000)
        engine.users['an_user'].resources.basic_materials_income = 1
        engine.users['an_user'].resources.advanced_materials_income = 1
        engine.users['an_user'].resources.money_income = 1
        engine.update_world(timestamp=2100)

        self.assertEqual(engine.users['an_user'].resources.basic_materials, 1100)
        self.assertEqual(engine.users['an_user'].resources.advanced_materials, 1100)
        self.assertEqual(engine.users['an_user'].resources.money, 1100)

    # def test_events_user_spoke(self):
        # engine = core.GameEngine()
        # engine.user_logged_in('an_user', timestamp=1000)
        # engine.update_world(timestamp=1050)
        # self.assertEqual(events, {
            # 'an_user': {
                # 'new_level': 6,
            # }
        # })
        # engine.user_room_message('an_user', 'some_message', timestamp=1051)
        # engine.update_world(timestamp=1053)
        ##would not trigger the lower level events again
        # self.assertEqual(events, {})

        ##user level should not decrement either.
        # self.assertEqual(engine.users['an_user']['level'], 6)
        
    def test_backwards_in_time_failure(self):
        engine = core.GameEngine()
        engine.user_logged_in('an_user', timestamp=1000)
        engine.update_world(timestamp=1050)
        self.assertRaises(core.TimeOutofBounds, engine.update_world, timestamp=999)
            
    def test_log_in_between_ticks(self):
        engine = core.GameEngine()
        engine.update_world(timestamp=100)
        engine.user_logged_in('an_user', timestamp=150)
        engine.users['an_user'].resources.basic_materials_income = 1
        engine.update_world(timestamp=200)
        self.assertEqual(engine.users['an_user'].resources.basic_materials, 50)
    
    def test_log_in_log_out_between_ticks(self):
        engine = core.GameEngine()
        engine.update_world(timestamp=100)
        engine.user_logged_in('an_user', timestamp=150)
        engine.users['an_user'].resources.basic_materials_income = 1
        engine.user_logged_out('an_user', timestamp=170)
        engine.update_world(timestamp=200)
        self.assertEqual(engine.users['an_user'].resources.basic_materials, 20)

    def test_event_engine_add(self):
        def some_event(name='foo'):
            return name

        engine = core.GameEngine()
        engine.add_event(some_event, name='foo')
        self.assertEqual(engine._engine_events[0].func, some_event)
        self.assertEqual(engine._engine_events[0].kw, {'name': 'foo'})

    def test_event_engine_backwards_in_time(self):
        def time_dependant_event(timestamp):
            return timestamp

        def time_independant_event():
            # if there is even such a thing.
            return

        engine = core.GameEngine()
        engine.update_world(timestamp=100)
        engine.add_event(time_dependant_event, timestamp=50)
        # timestamp argument magically forced to be the last time the
        # world was updated.

        self.assertEqual(engine._engine_events[0].kw['timestamp'], 100)

        # note that the order of events that got added to the engine do
        # matter very much.  i.e. if login and logout happened at about
        # the same time but the order they were added in were reversed,
        # bad things probably will happen.  Problem belongs to the user
        # of the engine, i.e. the chatroom interface.
