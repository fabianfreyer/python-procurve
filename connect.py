import paramiko
import getpass
import re
import time
import socket

class paramiko_shell(object):
    def __init__(self, host, username, password):
        self.rbuf = '' # Read buffer
        self._init_connection(host, username, password)

    def _init_connection(self, host, username, password):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(host, username=username, password=password)
        self.conn = self.ssh.invoke_shell()

    def ready(self, timeout):
        '''
        Wait until data is available on the connection,
        or timout is reached.
        '''
        tCheck = 0
        while not self.conn.recv_ready():
            time.sleep(1)
            tCheck+=1
            if tCheck >= timeout:
                raise socket.timeout

    def recv_until(self, until, keep=False, timeout=10, chunk_size=1024):
        chunks = []
        next_chunk = self.rbuf or self.recv_n(chunk_size)
        while until not in next_chunk:
            try:
                chunks.append(next_chunk)
                self.ready(timeout)
                next_chunk = self.recv_n(chunk_size)
            except socket.timeout:
                chunks.append(next_chunk)
                self.rbuf = ''.join(chunks)
                raise
        next_chunk, self.rbuf = next_chunk.split(until, 1)
        chunks.append(next_chunk)
        if keep:
            chunks.append(until)
        return ''.join(chunks)

    def recv(self, chunk_size=1024):
        '''
        read bytes from the connection until no data is available
        '''
        chunks = [self.rbuf or self.recv_n(chunk_size)]
        while self.conn.recv_ready():
            chunks.append(self.recv_n(chunk_size))
        self.rbuf = ''
        return ''.join(chunks)

    def recv_n(self, length):
        '''
        Read n bytes off the connection, non-blocking.
        '''
        if not self.conn.recv_ready():
            return ''

        if length <= len(self.rbuf):
            self.rbuf = self.rbuf[length:]
            message = self.rbuf[:length]
        else:
            message = self.conn.recv(length-len(self.rbuf))
            procurve_re1 = re.compile(r'(\[\d+[HKJ])|(\[\?\d+[hl])|(\[\d+)|(\;\d+\w?)')
            procurve_re2 = re.compile(r'([E]\b)')
            procurve_re3 = re.compile(ur'[\u001B]+') #remove stupid escapes
            message = procurve_re1.sub("", message)
            message = procurve_re2.sub("", message)
            message = procurve_re3.sub("", message)
            message = self.rbuf + message
            self.rbuf = ''
        return message

    def send(self, data):
        self.conn.send(data)

class procurve(paramiko_shell):
    class _contextmanager(object):
        def __init__(self, switch, context):
            self.switch = switch
            self.context = context
        def __enter__(self):
            self.switch.enter(self.context)
        def __exit__(self, exc_type, exc_value, exc_tb):
            self.switch.exit()
            return False

    def __init__(self, host, username, password):
        super(self.__class__, self).__init__(host, username, password)
        self.escape_ready()
        self.cmd('no page') # Turn off stupid paging

    def escape_ready(self):
        '''
        Escape the welcome screen, and get the prompt variable
        '''
        self.ready(10)
        self.recv()
        self.send('\n')
        self.ready(10)
        prompt = self.recv()
        # Parse the prompt and set up the context stack
        self.stack = []
        if '#' in prompt:
            self.stack.append('enable')
        self.ps1, self.ps2 = re.split('[$#]', prompt, 1)

    @property
    def prompt(self):
        '''
        Construct the prompt from the current context
        '''
        delim = '#' if 'enable' in self.stack else '$'
        context = [i for i in self.stack if i!='enable']
        context = '(%s)' % context[-1] if context else ''
        return ''.join([self.ps1, context, delim, self.ps2])

    def cmd(self, command):
        self.send(command+'\n')
        return self.recv_until(self.prompt)

    @property
    def config(self):
        return self.cmd('show config');

    def context(self, context):
        return self._contextmanager(self, context)

    def enter(self, context):
        '''
        enter a context, and push it to the context stack
        '''
        self.stack.append('-'.join(context.split(' ')))
        self.cmd(context)

    def exit(self):
        '''
        exit the last entered context, and remove it from the
        context stack
        '''
        context = self.stack.pop()
        self.cmd('exit')
        return context

    def enable(self, username, password):
        raise NotImplementedError
