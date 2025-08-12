"""Credential_Manger"""
import os
import json
import sys
import platform
import copy
import re
from pathlib import Path
from cryptography.fernet import Fernet
from threading import Lock
import getpass

from .base import MyBaseClass

class Credential_Manger(MyBaseClass):

    # PRIVATE_FUNCTIONS
    # =========================================================================
    def __init__(self: object, log: object=None, raise_exception_level: int=sys.maxsize, class_id: int=None, instance_name=__name__, key=b'yxlMhDvwpIl395OwUviVStNUvt5ZsaCNEH7kzC8bChc=') -> None:
        super().__init__(log=log, class_id=class_id, instance_name=instance_name)
        self._credential_dict = {}
        # Note to change generate a different key use Fernet.generate_key()
        self._fernet = Fernet(key)
        self.lock = Lock()
        base_name = 'zy2_no81a7cyz'

        self.os_type = platform.system()
        self.credential_file_path = '' 
        if self.os_type == "Windows":
            folder = 'cask$'
            folder_path = os.path.join(Path.home(), folder)
            if os.path.exists(folder_path) is False:
                os.makedirs(folder_path, exist_ok=True, mode=0o700)

            self.credential_file_path = os.path.join(folder_path, "zy2_no81a7cyz")

        elif self.os_type == "Linux":
            folder = '.cask'
            folder_path = os.path.join(Path.home(), folder)
            if os.path.exists(folder_path) is False:
                os.makedirs(folder_path, exist_ok=True,mode=0o700)

            self.credential_file_path = os.path.join(folder_path, ".zy2_no81a7cyz")
        elif self.os_type == "Darwin":
            folder = '.cask'

            folder_path = os.path.join(Path.home(), folder)
            if os.path.exists(folder_path) is False:
                os.makedirs(folder_path, exist_ok=True, mode=0o700)
            
            self.credential_file_path = os.path.join(folder_path, ".zy2_no81a7cyz")
        else:
            raise Exception(f"Unknown operating system: {self.os_type}")

        self.read()

    def _process_fields(self, section:str, field_dict: dict) -> dict:
        return_dict = self.gen_rs()

        if field_dict:
            if isinstance(field_dict, dict):
                keys = field_dict.keys()
                if len(keys) > 0:
                    for key in keys:
                        self._credential_dict[section][key] = copy.deepcopy(field_dict[key])
            else:
                self.add_error(return_dict, 'Expected additional_field_dict parameter to be a dict not %s' % type(field_dict))
        return return_dict

    def _write(self: object) -> dict:
        return_dict = self.gen_rs()
        file_contents = json.dumps(self._credential_dict)
        file_contents = self._fernet.encrypt(file_contents.encode('utf-8'))
        with open(self.credential_file_path, 'wb') as fp_out:
            fp_out.write(file_contents)
        return return_dict

    # PUBLIC FUNCTIONS
    # =========================================================================
    def add(self: object, section: str, field_dict: dict, overwrite: bool=False, auto_save: bool=True) -> dict:
        return_dict = self.gen_rs()
        with self.lock:
            if section in self._credential_dict and overwrite is False:
                self.add_error(return_dict, "The section [%s] already exists and the overwrite flag is false" % section)

            if return_dict['rc'] == 0:
                self._credential_dict[section] = {}

                result_dict = self._process_fields(section, field_dict)
                
                if self.check(result_dict, return_dict):
                    if auto_save:
                        self._write()
        return return_dict

    def delete(self: object, section:str, auto_save: bool=True) -> dict:
        return_dict = self.gen_rs()
        with self.lock:
            if section in self._credential_dict:
                del self._credential_dict[section]
                if auto_save:
                    self._write()
            else:
                self.add_error(return_dict, 'Section [%s] does not exist.' % section)
        return return_dict

    def get(self: object, section: str) -> dict:
        return_dict = self.gen_rs()
        with self.lock:
            if section in self._credential_dict:
                return_dict['contents'] = {}
                for key in section:
                    return_dict['contents'][key] = self._credential_dict[key] 
            else:
                self.add_error(return_dict, 'Section [%s] does not exist.' % section)
        return return_dict

    def get_password(self: object, prompt: str, retries: int=3, min_size: int=1, max_size: int=0, regex_pattern: str=None) -> dict:
        return_dict = self.gen_rs()

        if regex_pattern:
            regex = re.compile(regex_pattern)
        else:
            regex = None

        for i in range(0, retries):
            prompt_str = '%s [try: %s of %s]' % (prompt.strip(), i+1, retries)
            try:
                password = getpass.getpass(prompt_str)
            except Exception as error:
                print('ERROR:', error)
                password = None
                continue       

            if password:
                password = password.strip()

                password_length = len(password)

                if password_length < min_size:
                    password = None
                    print('Password must be at least %s characters long' % min_size)
                    continue

                if max_size > 0:
                    if password_length > max_size:
                        password = None
                        print('Password must not be greater then %s characters long' % max_size)
                        continue                   

                if regex:
                    result = regex.search(password)
                    if result:
                        pass
                    else:
                        password = None
                        print("Password did not pass regex pattern %s" % regex_pattern)
                        continue

                break
            else:
                print("Password cannot be None")
                continue

        return_dict['password'] = password

        if password is None:
            self.add_error(return_dict,"Failed to resolve the password. See console output for the reason.")
        return return_dict


    def get_sections(self: object) -> list:
        return_list = []
        with self.lock:
            return_list = list(self._credential_dict.keys())
        return return_list

    def modify(self: object, section: str, field_dict: dict, auto_save: bool=True) -> dict:
        return_dict = self.gen_rs()
        with self.lock:
            if section in self._credential_dict:
                self._credential_dict[section] = {}

                result_dict = self._process_fields(section, field_dict)
                if self.check(result_dict, return_dict):
                    if auto_save:
                        self._write()
            else:
                self.add_error(return_dict, 'Section [%s] does not exist.' % section)
        return return_dict

    def read(self: object) -> dict:
        return_dict = self.gen_rs()
        self._credential_dict = {}
        with self.lock:
            if os.path.exists(self.credential_file_path):
                with open(self.credential_file_path, 'rb') as fp_in:
                    file_contents = fp_in.read()
                if file_contents:
                    if len(file_contents) > 0:
                        file_contents = self._fernet.decrypt(file_contents)
                        self._credential_dict = json.loads(file_contents.decode('utf-8'))
        return return_dict

    def save(self: object) -> dict:
        return_dict = self.gen_rs()
        with self.lock:
            self._write()
        return return_dict