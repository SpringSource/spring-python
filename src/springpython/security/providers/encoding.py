"""
   Copyright 2006-2008 Greg L. Turnquist, All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.       
"""
import logging
import md5
import sha

class PasswordEncoder(object):
    """Interface for performing authentication operations on a password."""
    
    def encodePassword(self, rawPass, salt):
        """Encodes the specified raw password with an implementation specific algorithm."""
        raise NotImplementedError()
    
    def isPasswordValid(self, encPass, rawPass, salt):
        """Validates a specified "raw" password against an encoded password."""
        raise NotImplementedError()
    
class BasePasswordEncoder(PasswordEncoder):
    """Convenience base for all password encoders."""
    
    def __init__(self):
        super(BasePasswordEncoder, self).__init__()
        self.ignorePasswordCase = False
        self.logger = logging.getLogger("springpython.security.providers.BasePasswordEncoder")

    def mergePasswordAndSalt(self, password, salt, strict):
        """
        Used by subclasses to generate a merged password and salt String.
        The generated password will be in the form of 'password{salt}'.
        A None can be passed to either parameter, and will be handled correctly. If the salt is None or empty,
        the resulting generated password will simply be the passed password. The __str__ method of the salt will be used to represent the salt.
        """
        if password is None:
            password = ""

        if strict and salt is not None:
            if "{" in str(salt) or "}" in str(salt):
                raise ValueError("Cannot use { or } in salt.__str__")

        if salt is None or salt == "":
            return password
        else:
            return password + "{" + str(salt) + "}"


class PlaintextPasswordEncoder(BasePasswordEncoder):
    """
    Plaintext implementation of PasswordEncoder.

    As callers may wish to extract the password and salts separately from the encoded password,
    the salt must not contain reserved characters (specifically '{' and '}').
    """

    def __init__(self):
        super(PlaintextPasswordEncoder, self).__init__()
        self.logger = logging.getLogger("springpython.security.providers.PlaintextPasswordEncoder")
        
    def encodePassword(self, rawPass, salt):
        """Encodes the specified raw password with an implementation specific algorithm."""
        return self.mergePasswordAndSalt(rawPass, salt, True)

    def isPasswordValid(self, encPass, rawPass, salt):
        """Validates a specified "raw" password against an encoded password."""
        pass1 = encPass + ""

        # Strict delimiters is false because pass2 never persisted anywhere
        # and we want to avoid unnecessary exceptions as a result (the
        # authentication will fail as the encodePassword never allows them)
        pass2 = self.mergePasswordAndSalt(rawPass, salt, False)
        
        if not self.ignorePasswordCase:
            return pass1 == pass2
        else:
            return pass1.upper() == pass2.upper()

class AbstractOneWayPasswordEncoder(BasePasswordEncoder):
    """
    This is an abstract one-way hashing encoder. It is abstract because the
    subclasses have to plugin their strategy.
    """
    def __init__(self):
        super(AbstractOneWayPasswordEncoder, self).__init__()
        self.onewayHasher = None
        self.logger = logging.getLogger("springpython.security.providers.AbstractOneWayPasswordEncoder")
        
    def encodePassword(self, rawPass, salt):
        """Encodes the specified raw password with an implementation specific algorithm."""
        hasher = self.onewayHashStrategy.new()
        if not self.ignorePasswordCase:
            hasher.update(self.mergePasswordAndSalt(rawPass, salt, False))
        else:
            hasher.update(self.mergePasswordAndSalt(rawPass.lower(), salt, False))
        return hasher.hexdigest()

    def isPasswordValid(self, encPass, rawPass, salt):
        """Validates a specified "raw" password against an encoded password."""
        pass1 = encPass + ""

        # Strict delimiters is false because pass2 never persisted anywhere
        # and we want to avoid unnecessary exceptions as a result (the
        # authentication will fail as the encodePassword never allows them)
        pass2 = self.mergePasswordAndSalt(rawPass, salt, False)

        hasher = self.onewayHashStrategy.new()
        if self.ignorePasswordCase:
            hasher.update(pass2.lower())
        else:
            hasher.update(pass2)
        pass2 = hasher.hexdigest()
        
        if not self.ignorePasswordCase:
            return pass1 == hasher.hexdigest()
        else:
            return pass1.lower() == hasher.hexdigest()

class Md5PasswordEncoder(AbstractOneWayPasswordEncoder):
    """
    MD5 implementation of PasswordEncoder.
    
    If a None password is presented, it will be treated as an empty String ("") password.
    
    As MD5 is a one-way hash, the salt can contain any characters.
    """

    def __init__(self):
        super(Md5PasswordEncoder, self).__init__()
        self.onewayHashStrategy = md5
        self.logger = logging.getLogger("springpython.security.providers.Md5PasswordEncoder")
        
class ShaPasswordEncoder(AbstractOneWayPasswordEncoder):
    """
    SHA implementation of PasswordEncoder.
    
    If a None password is presented, it will be treated as an empty String ("") password.
    
    As SHA is a one-way hash, the salt can contain any characters.
    """

    def __init__(self):
        super(ShaPasswordEncoder, self).__init__()
        self.onewayHashStrategy = sha
        self.logger = logging.getLogger("springpython.security.providers.ShaPasswordEncoder")
