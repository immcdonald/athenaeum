"""
my base class
"""
import logging
import sys
import os
import inspect
import itertools
from pprint import pformat as fp

class MyBaseClass(object):
    OK = 0
    ERROR = 1
    _id_iter = itertools.count()

    # Private
    # ========================================================================
    def __init__(self: object, log: object=None, raise_exception_level: int=sys.maxsize, class_id: int=None, instance_name=__name__) -> None:
        self._instance_name = instance_name
        if class_id:
            self._unique_id = class_id
        else:
            self._unique_id = next(self._id_iter)
        
        self._raise_exception_level = raise_exception_level

        if log:
            self._log = log
        else:
            self._init_logging(instance_name)
        
    def _init_logging(self: object, instance_name: str) -> None:
        if instance_name == __name__:
            instance_name = "%s_%04d" % (__name__, self._unique_id)
        
        self._log = logging.getLogger(instance_name)

        # Only create one set of handlers for this logging instance.
        # If you don't do this check you end up with multiple handlers which means if you 
        # use one self.log.info("Hello World") call for instnace you could get the same output multiple times.
        if self._log.hasHandlers() is False:
            stream_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            stream_handler = logging.StreamHandler() 
            stream_handler.setFormatter(stream_format)
            self._log.setLevel(logging.DEBUG)
            self._log.addHandler(stream_handler) 

    # Public
    # ========================================================================
    def add_error(self: object, input_dict: dict, error: str, rel: int=0, rc: int=ERROR, stack_adjustment:int=2) -> list:
        error_data = {'error': error} 

        stack_count = len(inspect.stack())

        if stack_adjustment >= stack_count:
            raise Exception ('Stack adjustment %s is greater then the current stack count %s\nError: %s\nInput Dict: %s\n' % (stack_adjustment, error, pf(input_dict)))

        frame, filename, line_number, function_name, lines, index = inspect.stack()[stack_adjustment]
        
        error_data['filename'] = filename
        error_data['line_number'] = line_number
        error_data['function_name'] = function_name
        error_data['lines'] = lines
        error_data['index'] = index
        error_data['raise_exception_level'] = rel

        if rel >= self._raise_exception_level:
            output = 'add_error function called with raise_exception_level [%s] which is >= threshold level [%d]\n' % (rel, self._raise_exception_level)
            output += 'Inspect Filename: %s\n' % error_data['filename']
            output += 'Inspect Line Number: %s\n' % error_data['line_number']
            output += 'Inspect Function Name %s\n' % error_data['function_name']
            output += 'Inspect Lines %s\n' % error_data['lines']
            output += 'Inspect Index: %s\n' % error_data['index']
            output += 'Error: %s\n\n' % error_data['error']
            raise Exception(output)

        # First check to see if input_dict['rc'] == self.OK. 
        # if so then assign it the value of rc.
        if input_dict['rc'] == self.OK:
            input_dict['rc'] = rc

        input_dict['errors'].append(error_data)
        return [error_data]
    
    def check(self: object, result_dict: dict, return_dict: dict, copy: bool=True) -> bool:
        return_bool = True
        
        if copy:
            if result_dict is not None:
                for key in result_dict.keys():
                    if key == 'rc':
                        if return_dict['rc'] != self.OK:
                            continue
                    if key == 'errors':
                        return_dict[key] += result_dict[key]
                    else:
                        return_dict[key] = result_dict[key]
            else:
                raise Exception('Provided result dict is None!')

        if result_dict['rc'] != self.OK:
            return_bool = False
            if copy is False:
                if return_dict['rc'] == self.OK:
                    return_dict['rc'] = result_dict['rc']
                return_dict['errors'] += result_dict['errors']
        return return_bool

    def error_list_to_str(self:object, error_list: list, show_location: bool=False, show_line: bool=False, show_error_delimiter:bool=True) -> str:
        return_str = ''
        error_count = len(error_list)

        for error_index in range(0, error_count):
            if error_count > 1:
                return_str += 'Error %4d of %4d %s\n' % (error_index + 1, error_count, '=' * 60)

            if show_location:
                return_str += '[%s:%s:%s]' % (error_list[error_index]['filename'], error_list[error_index]['line_number'], error_list[error_index]['function_name'])

            return_str += ' %s' % error_list[error_index]['error']

            if show_line:
                if len(error_list[error_index]['lines']) > 1:
                    return_str += 'Code:\n'
                    for line in error_list[error_index]['lines']:
                         return_str += line.strip()
                else:
                    return_str += ' Code %s' % error_list[error_index]['lines'][0].strip()

            return_str += '\n'
        return return_str

    def get_id(self: object) -> int:
        return self._unique_id 

    def get_log(self: object) -> object:
        return self._log

    def gen_rs(self: object) -> dict:
        return {'rc': 0, 'errors': []}

    def print_error(self: object, result_dict: dict, show_location: bool=False, show_line: bool=False) -> None:
        if 'errors' in result_dict:
            if len(result_dict['errors']) > 0:
                error_str = self.error_list_to_str(result_dict['errors'], show_location=show_location, show_line=show_line)
                self._log.error(error_str)
            else:
                self._log.error('No errors in the error list.')
        else:
            self._log.error('errors key is not present in passed dictionary.')

    def sync_result(self: object, source: dict, dest: dict) -> dict:
        return_dict = self.gen_rs()

        if 'rc' in source:
            if 'rc' in dest:
                dest['rc'] = source['rc']

                if 'errors' in source:
                    if 'errors' in dest:
                        dest['errors'] += source['errors']
                    else:
                        self.add_error(return_dict,'Expected provided dest dict to have errors key, but it did not.', rel=1)
                else:
                    self.add_error(return_dict, 'Expected provided src dict to have errors key, but it did not.', rel=1)
            else:
                self.add_error(return_dict, 'Expected provided dest dict to have rc key, but it did not.', rel=1)
        else:
            self.add_error(return_dict, 'Expected provided src dict to have rc key, but it did not.', rel=1)
        return return_dict

    def pf(self:object, value) -> str:
        return pf(value)