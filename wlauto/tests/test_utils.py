#    Copyright 2013-2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


# pylint: disable=R0201
from unittest import TestCase

from nose.tools import raises, assert_equal, assert_not_equal, assert_true  # pylint: disable=E0611

from wlauto.utils.android import check_output
from wlauto.utils.misc import merge_dicts, merge_lists, TimeoutError
from wlauto.utils.types import (list_or_integer, list_or_bool, caseless_string, arguments,
                                ParameterDict)


class TestCheckOutput(TestCase):

    def test_ok(self):
        check_output("python -c 'import time; time.sleep(0.1)'", timeout=0.5, shell=True)

    @raises(TimeoutError)
    def test_bad(self):
        check_output("python -c 'import time; time.sleep(1)'", timeout=0.5, shell=True)


class TestMerge(TestCase):

    def test_dict_merge(self):
        base = {'a': 1, 'b': {'x': 9, 'z': 10}}
        other = {'b': {'x': 7, 'y': 8}, 'c': [1, 2, 3]}
        result = merge_dicts(base, other)
        assert_equal(result['a'], 1)
        assert_equal(result['b']['x'], 7)
        assert_equal(result['b']['y'], 8)
        assert_equal(result['b']['z'], 10)
        assert_equal(result['c'], [1, 2, 3])

    def test_merge_dict_lists(self):
        base = {'a': [1, 3, 2]}
        other = {'a': [3, 4, 5]}
        result = merge_dicts(base, other)
        assert_equal(result['a'], [1, 3, 2, 3, 4, 5])
        result = merge_dicts(base, other, list_duplicates='first')
        assert_equal(result['a'], [1, 3, 2, 4, 5])
        result = merge_dicts(base, other, list_duplicates='last')
        assert_equal(result['a'], [1, 2, 3, 4, 5])

    def test_merge_lists(self):
        result = merge_lists([1, 2, 3], 7)
        assert_equal(result, [1, 2, 3, 7])
        result = merge_lists([1, 2, 3], 1, duplicates='last')
        assert_equal(result, [2, 3, 1])

    @raises(ValueError)
    def test_type_mismatch(self):
        base = {'a': [1, 2, 3]}
        other = {'a': 'test'}
        merge_dicts(base, other, match_types=True)


class TestTypes(TestCase):

    def test_list_or_conversion(self):
        assert_equal(list_or_integer([1, '2', 3]), [1, 2, 3])
        assert_equal(list_or_integer('0xF'), [15,])
        assert_equal(list_or_bool('False'), [False,])

    def test_caseless_string(self):
        cs1 = caseless_string('TeSt')
        assert_equal(cs1, 'TeSt')
        assert_equal('test', cs1)
        assert_equal(cs1[0], 'T')
        assert_not_equal(cs1[0], 't')
        assert_not_equal(cs1, 'test2')

    def test_arguments(self):
        assert_equal(arguments('--foo 7 --bar "fizz buzz"'),
                     ['--foo', '7', '--bar', 'fizz buzz'])
        assert_equal(arguments(['test', 42]), ['test', '42'])

class TestParameterDict(TestCase):

    # Define test parameters
    orig_params = {
                        'string' : 'A Test String',
                        'string_list' : ['A Test', 'List', 'With', '\n in.'],
                        'bool_list' : [False, True, True],
                        'int' : 42,
                        'float' : 1.23,
                        'long' : long(987),
                        'none' : None,
                        }

    def setUp(self):
        self.params = ParameterDict()
        self.params['string'] = self.orig_params['string']
        self.params['string_list'] = self.orig_params['string_list']
        self.params['bool_list'] = self.orig_params['bool_list']
        self.params['int'] = self.orig_params['int']
        self.params['float'] = self.orig_params['float']
        self.params['long'] = self.orig_params['long']
        self.params['none'] = self.orig_params['none']

    # Test values are encoded correctly
    def test_getEncodedItems(self):
        encoded = {
                    'string' : 'ssA%20Test%20String',
                    'string_list' : 'slA%20Test0newelement0List0newelement0With0newelement0%0A%20in.',
                    'bool_list' : 'blFalse0newelement0True0newelement0True',
                    'int' : 'is42',
                    'float' : 'fs1.23',
                    'long' : 'ds987',
                    'none' : 'nsNone',
                   }
        # Test iter_encoded_items
        for k, v in self.params.iter_encoded_items():
            assert_equal(v, encoded[k])

        # Test get single encoded value
        assert_equal(self.params.get_encoded_value('string'), encoded['string'])
        assert_equal(self.params.get_encoded_value('string_list'), encoded['string_list'])
        assert_equal(self.params.get_encoded_value('bool_list'), encoded['bool_list'])
        assert_equal(self.params.get_encoded_value('int'), encoded['int'])
        assert_equal(self.params.get_encoded_value('float'), encoded['float'])
        assert_equal(self.params.get_encoded_value('long'), encoded['long'])
        assert_equal(self.params.get_encoded_value('none'), encoded['none'])

    # Test it behaves like a normal dict
    def test_getitem(self):
        assert_equal(self.params['string'], self.orig_params['string'])
        assert_equal(self.params['string_list'], self.orig_params['string_list'])
        assert_equal(self.params['bool_list'], self.orig_params['bool_list'])
        assert_equal(self.params['int'], self.orig_params['int'])
        assert_equal(self.params['float'], self.orig_params['float'])
        assert_equal(self.params['long'], self.orig_params['long'])
        assert_equal(self.params['none'], self.orig_params['none'])

    def test_get(self):
        assert_equal(self.params.get('string'), self.orig_params['string'])
        assert_equal(self.params.get('string_list'), self.orig_params['string_list'])
        assert_equal(self.params.get('bool_list'), self.orig_params['bool_list'])
        assert_equal(self.params.get('int'), self.orig_params['int'])
        assert_equal(self.params.get('float'), self.orig_params['float'])
        assert_equal(self.params.get('long'), self.orig_params['long'])
        assert_equal(self.params.get('none'), self.orig_params['none'])

    def test_contains(self):
        assert_true(self.orig_params['string'] in self.params.values())
        assert_true(self.orig_params['string_list'] in self.params.values())
        assert_true(self.orig_params['bool_list'] in self.params.values())
        assert_true(self.orig_params['int'] in self.params.values())
        assert_true(self.orig_params['float'] in self.params.values())
        assert_true(self.orig_params['long'] in self.params.values())
        assert_true(self.orig_params['none'] in self.params.values())

    def test_pop(self):
        assert_equal(self.params.pop('string'), self.orig_params['string'])
        assert_equal(self.params.pop('string_list'), self.orig_params['string_list'])
        assert_equal(self.params.pop('bool_list'), self.orig_params['bool_list'])
        assert_equal(self.params.pop('int'), self.orig_params['int'])
        assert_equal(self.params.pop('float'), self.orig_params['float'])
        assert_equal(self.params.pop('long'), self.orig_params['long'])
        assert_equal(self.params.pop('none'), self.orig_params['none'])

        self.params['string'] = self.orig_params['string']
        assert_equal(self.params.popitem(), ('string', self.orig_params['string']))

    def test_iteritems(self):
        for k, v in self.params.iteritems():
            assert_equal(v, self.orig_params[k])

    def test_parameter_dict_update(self):
        params_1 = ParameterDict()
        params_2 = ParameterDict()

        # Test two ParameterDicts
        params_1['string'] = self.orig_params['string']
        params_1['string_list'] = self.orig_params['string_list']
        params_1['bool_list'] = self.orig_params['bool_list']
        params_2['int'] = self.orig_params['int']
        params_2['float'] = self.orig_params['float']
        params_2['long'] = self.orig_params['long']
        params_2['none'] = self.orig_params['none']

        params_1.update(params_2)
        assert_equal(params_1, self.params)

        # Test update with normal dict
        params_3 = ParameterDict()
        std_dict = dict()

        params_3['string'] = self.orig_params['string']
        std_dict['string_list'] = self.orig_params['string_list']
        std_dict['bool_list'] = self.orig_params['bool_list']
        std_dict['int'] = self.orig_params['int']
        std_dict['float'] = self.orig_params['float']
        std_dict['long'] = self.orig_params['long']
        std_dict['none'] = self.orig_params['none']

        params_3.update(std_dict)
        for key in params_3.keys():
            assert_equal(params_3[key], self.params[key])
