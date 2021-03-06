import os
import re

from plugins import Plugin
from events import ServerOutput


class Trigger(Plugin):
    command = "msg {user} {message}"
    path = "triggers.txt"
    
    triggers = {}
    
    def setup(self):
        if self.path and os.path.exists(self.path):
            f = open(self.path, 'r')
            for l in f:
                m = re.match('^\!?([^,]+),(.+)$', l)
                if m:
                    a, b = m.groups()
                    c = self.triggers.get(a, [])
                    c.append(b)
                    self.triggers[a] = c
            f.close()
            
            if self.triggers:
                self.register(self.trigger, ServerOutput, pattern='<([A-Za-z0-9_]{1,16})> \!(\w+)')
    
    def trigger(self, event):
        user, trigger = event.match.groups()
        if trigger in self.triggers:
            for line in self.triggers[trigger]:
                self.send(self.command.format(user=user, message=line), parseColors=True)
