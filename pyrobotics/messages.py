import threading
import re
from abc import ABCMeta

class MessageTypes(object):
    '''
    Internal pseudo-enum to set the type of message to a message.
    
    The existing values are:
    
        * MessageTypes.COMMAND
        * MessageTypes.RESPONSE
        * MessageTypes.SHARED_VAR
    '''
    __metaclass__ = ABCMeta
    COMMAND = 1
    RESPONSE = 2
    SHARED_VAR = 3

class Message(object):
    '''
    Internal abstract class, parent of Command, Response and SharedVar classes.
    
    All derived classes of Message have the members:
    
        name
            The command name. (The actual text that is sent and is included as key in a functionMap in the module that process it).
            
        params
            The parameters for this message, they are always serialized and received as string.
            In case of a Command object, it represents the parameters of the command.
            In the case of a Response object, it represents the response generated by a command.
            If a command is not meant to produce any response additional to the boolean result of successful or unsuccessful,
            it does not matter what this filed has, although it is usually the original parameters sent by the command.
            
        type
            One of the class variables from :class:`MessageTypes`
            
        isNotification
            This value is ``False`` in Command and Response objects, and ``True`` in SharedVar objects.
    
    '''
    
    __metaclass__ = ABCMeta

    def __init__(self, commandName, params = None):
        self.name = commandName
        if params:
            self.params = params
        else:
            self.params = ''
        self._id = -1
        self.type = MessageTypes.RESPONSE
        self.isNotification = False
    
    def __eq__(self, other):
        return self.name == other.name and self._id == other._id
    
    def __hash__(self):
        return hash(self.name + str(self._id))
    
    def _isStandardCommand(self):
        return self.name in set(['busy',
                             'alive',
                             'ready'])
    def __repr__(self):
        textrep = self.name
        if not self._isStandardCommand():
            textrep += ' ' + Message._SerializeString(self.params)
        if self.type in [MessageTypes.RESPONSE, MessageTypes.SHARED_VAR]:
            textrep += ' ' + str(int(self.successful))
        if self._id > -1:
            textrep += ' @' + str(self._id)
        return textrep
    
    @classmethod
    def _DeserializeString(cls, data):
        
        if data == 'null':
            return None

        start = data.find('"')
        end = data.rfind('"')
        if start < 0 or end <= start:
            return None
    
        data = data[start+1:end]
        
        data = re.sub(r'(?<!\\)\\"', r'"', data)
        data = re.sub(r'\\\\\\"', r'\\"', data)
        
        data = re.sub(r"(?<!\\)\\'", r"'", data)
        data = re.sub(r"\\\\\\'", r"\\'", data)
    
        data = re.sub(r'(?<!\\)\\n', r'\n', data)
        data = re.sub(r'\\\\n', r'\\n', data)
    
        data = re.sub(r'(?<!\\)\\t', r'\t', data)
        data = re.sub(r'\\\\t', r'\\t', data)
    
        data = re.sub(r'(?<!\\)\\r', r'\r', data)
        data = re.sub(r'\\\\r', r'\\r', data)
    
        return data

    @classmethod
    def _SerializeString(cls, data):
        if data == None:
            return 'null'
        
        data = str(data)
    
        data = re.sub(r'\\n', r'\\\\n', data)
        data = re.sub(r'\n', r'\\n', data)
    
        data = re.sub(r'\\t', r'\\\\t', data)
        data = re.sub(r'\t', r'\\t', data)
    
        data = re.sub(r'\\r', r'\\\\r', data)
        data = re.sub(r'\r', r'\\r', data)
    
        data = re.sub(r'\\"', r'\\\\\\"', data)
        data = re.sub(r'(?<!\\)"', r'\\"', data)
        
        data = re.sub(r"\\'", r"\\\\\\'", data)
        data = re.sub(r"(?<!\\)'", r"\\'", data)
    
        data = '"' + data + '"'
    
        return data

class Command(Message):
    '''
    Creates a command object with *commandName* name and parameters *params*.
    
    This class should be instantiated every time a command is sent to the BlackBoad.
    '''
    _idCounter = 1
    _idLock = threading.Lock()
    
    _rx = re.compile(r'^((?P<src>[A-Za-z][A-Za-z\-]*)\s+)?(?P<cmd>[A-Za-z_]+)(\s+(?P<params>"(\\"|[^"])*"))?(\s+@(?P<id>\d+))?$')
    
    def __init__(self, commandName, params = "", idNum = None):
        
        super(Command, self).__init__(commandName, params)
        self.type = MessageTypes.COMMAND
        
        #Workaround for BB not returning ID on these commands:
        if commandName == 'write_var':
            return
        if idNum != None:
            self._id = idNum
        else:
            Command._idLock.acquire()
            self._id = Command._idCounter
            Command._idCounter += 1
            Command._idLock.release()
    
    @classmethod
    def Parse(cls, s):
        m = Command._rx.match(s)
        if not m:
            return None
        
        sCommand = m.group('cmd').lower()
        sParams = m.group('params')
        sId = m.group('id')
        idNum = -1
        if sId and len(sId) > 0:
            idNum = int(sId)
        if sParams:
            #sParams = sParams.replace("\\\"", "\"")
            sParams = Message._DeserializeString(sParams)
        return Command(sCommand, sParams, idNum)

class Response(Message):
    '''
    A Response object for the command *commandName*.
    
    A Response should include a boolean stating whether the execution was successful or unsuccessful,
    this is set by the parameter *successful*.
    
    The third field of the constructor is the response of the command, if this command is not meant to produce
    a response additional to the boolean result of successful or unsuccessful, it does not matter what this parameter is,
    although it is usually the original parameters sent by the command.
    
    The result of a Response object is stored in the member **result**.
    
    .. warning::
        
        Ideally no Response objects should be built with this constructor, but with the class method :func:`Response.FromCommandObject`.
        This is important because an internal id is generated to keep track of the commands and their responses.
    '''
    
    _rx = re.compile(r'^((?P<src>[A-Za-z][A-Za-z\-]*)\s+)?(?P<cmd>[A-Za-z_]+)(\s+(?P<params>"(\\"|[^"])*"))?\s+(?P<result>[10])(\s+@(?P<id>\d+))?$')
    
    def __init__(self, commandName, successful = False, response = ''):
        super(Response, self).__init__(commandName, response)
        self.type = MessageTypes.RESPONSE
        self.successful = successful
    
    @classmethod
    def Parse(cls, s):
        m = Response._rx.match(s)
        if not m:
            return None
        
        sCommand = m.group('cmd').lower()
        sParams = m.group('params').strip()
        sId = m.group('id')
        sResult = m.group('result')
        idNum = -1
        
        if sResult is None or (sResult != '1' and sResult != '0'):
            return None
        if sId and len(sId) > 0:
            idNum = int(sId)
                    
        successful = int(sResult == '1')
        
        if sParams:
            sParams = Message._DeserializeString(sParams)
        
        r = Response(sCommand, successful, sParams)
        r._id = idNum
        return r
    
    @classmethod
    def FromCommandObject(cls, commandObj, successful = False, response = None):
        '''
        Builds a Response object from a Command object and sets its successful and response members. (See :meth:`Response.__init__`)
        
        This method should be used in every command handler function to create a response
        from the Command object it receives as parameter. (See examples in :ref:`Creating a command handler <creating_a_command_handler>`).
        '''
        if not response:
            response = commandObj.params
        
        if not isinstance(commandObj, Command):
            raise Exception('commandObj not instance of Command in Response.FromCommandObject.')
        
        r = cls(commandObj.name, successful, response)
        r._id = commandObj._id
        return r
