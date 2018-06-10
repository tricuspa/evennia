"""
Unit tests for the prototypes and spawner

"""

from random import randint
import mock
from anything import Anything, Something
from evennia.utils.test_resources import EvenniaTest
from evennia.prototypes import spawner, prototypes as protlib

from evennia.prototypes.prototypes import _PROTOTYPE_TAG_META_CATEGORY

_PROTPARENTS = {
    "NOBODY": {},
    "GOBLIN": {
        "key": "goblin grunt",
        "health": lambda: randint(1, 1),
        "resists": ["cold", "poison"],
        "attacks": ["fists"],
        "weaknesses": ["fire", "light"]
    },
    "GOBLIN_WIZARD": {
        "prototype": "GOBLIN",
        "key": "goblin wizard",
        "spells": ["fire ball", "lighting bolt"]
    },
    "GOBLIN_ARCHER": {
        "prototype": "GOBLIN",
        "key": "goblin archer",
        "attacks": ["short bow"]
    },
    "ARCHWIZARD": {
        "attacks": ["archwizard staff"],
    },
    "GOBLIN_ARCHWIZARD": {
        "key": "goblin archwizard",
        "prototype": ("GOBLIN_WIZARD", "ARCHWIZARD")
    }
}


class TestPrototypes(EvenniaTest):
    pass


class TestSpawner(EvenniaTest):

    def setUp(self):
        super(TestSpawner, self).setUp()
        self.prot1 = {"prototype_key": "testprototype"}

    def test_spawn(self):
        obj1 = spawner.spawn(self.prot1)
        # check spawned objects have the right tag
        self.assertEqual(list(protlib.search_objects_with_prototype("testprototype")), obj1)
        self.assertEqual([o.key for o in spawner.spawn(
                          _PROTPARENTS["GOBLIN"], _PROTPARENTS["GOBLIN_ARCHWIZARD"],
                          prototype_parents=_PROTPARENTS)], ['goblin grunt', 'goblin archwizard'])


class TestUtils(EvenniaTest):

    def test_prototype_from_object(self):
        self.maxDiff = None
        self.obj1.attributes.add("test", "testval")
        self.obj1.tags.add('foo')
        new_prot = spawner.prototype_from_object(self.obj1)
        self.assertEqual(
            {'attrs': [('test', 'testval', None, [''])],
             'home': Something,
             'key': 'Obj',
             'location': Something,
             'locks': ['call:true()',
                       'control:perm(Developer)',
                       'delete:perm(Admin)',
                       'edit:perm(Admin)',
                       'examine:perm(Builder)',
                       'get:all()',
                       'puppet:pperm(Developer)',
                       'tell:perm(Admin)',
                       'view:all()'],
             'prototype_desc': 'Built from Obj',
             'prototype_key': Something,
             'prototype_locks': 'spawn:all();edit:all()',
             'prototype_tags': [],
             'tags': [(u'foo', None, None)],
             'typeclass': 'evennia.objects.objects.DefaultObject'}, new_prot)

    def test_update_objects_from_prototypes(self):

        self.maxDiff = None
        self.obj1.attributes.add('oldtest', 'to_remove')

        old_prot = spawner.prototype_from_object(self.obj1)

        # modify object away from prototype
        self.obj1.attributes.add('test', 'testval')
        self.obj1.aliases.add('foo')
        self.obj1.key = 'NewObj'

        # modify prototype
        old_prot['new'] = 'new_val'
        old_prot['test'] = 'testval_changed'
        old_prot['permissions'] = 'Builder'
        # this will not update, since we don't update the prototype on-disk
        old_prot['prototype_desc'] = 'New version of prototype'

        # diff obj/prototype
        pdiff = spawner.prototype_diff_from_object(old_prot, self.obj1)

        self.assertEqual(
             pdiff,
             {'aliases': 'REMOVE',
              'attrs': 'REPLACE',
              'home': 'KEEP',
              'key': 'UPDATE',
              'location': 'KEEP',
              'locks': 'KEEP',
              'new': 'UPDATE',
              'permissions': 'UPDATE',
              'prototype_desc': 'UPDATE',
              'prototype_key': 'UPDATE',
              'prototype_locks': 'KEEP',
              'prototype_tags': 'KEEP',
              'test': 'UPDATE',
              'typeclass': 'KEEP'})

        # apply diff
        count = spawner.batch_update_objects_with_prototype(
            old_prot, diff=pdiff, objects=[self.obj1])
        self.assertEqual(count, 1)

        new_prot = spawner.prototype_from_object(self.obj1)
        self.assertEqual({'attrs': [('test', 'testval_changed', None, ['']),
                                    ('new', 'new_val', None, [''])],
                          'home': Something,
                          'key': 'Obj',
                          'location': Something,
                          'locks': ['call:true()',
                                    'control:perm(Developer)',
                                    'delete:perm(Admin)',
                                    'edit:perm(Admin)',
                                    'examine:perm(Builder)',
                                    'get:all()',
                                    'puppet:pperm(Developer)',
                                    'tell:perm(Admin)',
                                    'view:all()'],
                          'permissions': 'builder',
                          'prototype_desc': 'Built from Obj',
                          'prototype_key': Something,
                          'prototype_locks': 'spawn:all();edit:all()',
                          'prototype_tags': [],
                          'typeclass': 'evennia.objects.objects.DefaultObject'},
                         new_prot)


class TestProtLib(EvenniaTest):

    def setUp(self):
        super(TestProtLib, self).setUp()
        self.obj1.attributes.add("testattr", "testval")
        self.prot = spawner.prototype_from_object(self.obj1)

    def test_prototype_to_str(self):
        prstr = protlib.prototype_to_str(self.prot)
        self.assertTrue(prstr.startswith("|cprototype key:|n"))

    def test_check_permission(self):
        pass

class TestPrototypeStorage(EvenniaTest):

    def setUp(self):
        super(TestPrototypeStorage, self).setUp()
        self.maxDiff = None

        self.prot1 = spawner.prototype_from_object(self.obj1)
        self.prot1['prototype_key'] = 'testprototype1'
        self.prot1['prototype_desc'] = 'testdesc1'
        self.prot1['prototype_tags'] = [('foo1', _PROTOTYPE_TAG_META_CATEGORY)]

        self.prot2 = self.prot1.copy()
        self.prot2['prototype_key'] = 'testprototype2'
        self.prot2['prototype_desc'] = 'testdesc2'
        self.prot2['prototype_tags'] = [('foo1', _PROTOTYPE_TAG_META_CATEGORY)]

        self.prot3 = self.prot2.copy()
        self.prot3['prototype_key'] = 'testprototype3'
        self.prot3['prototype_desc'] = 'testdesc3'
        self.prot3['prototype_tags'] = [('foo1', _PROTOTYPE_TAG_META_CATEGORY)]

    def test_prototype_storage(self):

        prot1 = protlib.create_prototype(**self.prot1)

        self.assertTrue(bool(prot1))
        self.assertEqual(prot1, self.prot1)

        self.assertEqual(prot1['prototype_desc'], "testdesc1")

        self.assertEqual(prot1['prototype_tags'], [("foo1", _PROTOTYPE_TAG_META_CATEGORY)])
        self.assertEqual(
            protlib.DbPrototype.objects.get_by_tag(
                "foo1", _PROTOTYPE_TAG_META_CATEGORY)[0].db.prototype, prot1)

        prot2 = protlib.create_prototype(**self.prot2)
        self.assertEqual(
            [pobj.db.prototype
             for pobj in protlib.DbPrototype.objects.get_by_tag(
                 "foo1", _PROTOTYPE_TAG_META_CATEGORY)],
            [prot1, prot2])

        # add to existing prototype
        prot1b = protlib.create_prototype(
            prototype_key='testprototype1', foo='bar', prototype_tags=['foo2'])

        self.assertEqual(
            [pobj.db.prototype
             for pobj in protlib.DbPrototype.objects.get_by_tag(
                 "foo2", _PROTOTYPE_TAG_META_CATEGORY)],
            [prot1b])

        self.assertEqual(list(protlib.search_prototype("testprototype2")), [prot2])
        self.assertNotEqual(list(protlib.search_prototype("testprototype1")), [prot1])
        self.assertEqual(list(protlib.search_prototype("testprototype1")), [prot1b])

        prot3 = protlib.create_prototype(**self.prot3)

        # partial match
        self.assertEqual(list(protlib.search_prototype("prot")), [prot1b, prot2, prot3])
        self.assertEqual(list(protlib.search_prototype(tags="foo1")), [prot1b, prot2, prot3])

        self.assertTrue(str(unicode(protlib.list_prototypes(self.char1))))
