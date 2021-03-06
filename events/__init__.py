import inspect, sys, time

from twisted.internet import reactor, task

ACCEPTED = 1
FINISHED = 2

class Event:
    doc                = ""
    contains           = None
    requires           = tuple() # required kwargs
    requires_predicate = tuple() # required register() kwargs
    handled   = False
    cancelled = False
    
    def __init__(self, **args):
        left = list(self.requires)
        for n, v in args.iteritems():
            setattr(self, n, v)
            if n in left:
                left.remove(n)
        if len(left) > 0:
            raise Exception("Event type %s missing argument(s): %s" % (self.__class__.__name__, ", ".join(left)))
        
        if not self.contains:
            self.contains = set(self.requires)
        
        self.setup()
    
    def setup(self):
        pass
    
    def consider(self, r_args):
        return ACCEPTED

    def serialize(self):
        data = {k: getattr(self, k) for k in self.contains}
        data['class_name'] = self.__class__.__name__
        return data

    def __getitem__(self, item):
        try:
            return getattr(self, item)
        except AttributeError:
            raise IndexError


class EventDispatcher:
    registered = {}
    registered_ids = []

    def __init__(self, error_handler):
        self.error_handler = error_handler

    def register(self, callback, event_type, **predicate_args):
        if not event_type in self.registered:
            self.registered[event_type] = []
        d = self.registered[event_type]
        
        for p in event_type.requires_predicate:
            if not p in predicate_args:
                raise Exception("missing required predicate argument for %s: %s" % (event_type.__class__, p))
        
        d.append((callback, predicate_args))
        self.registered_ids.append((callback, event_type, predicate_args))
        return len(self.registered_ids)-1
    
    def unregister(self, ident):
        if len(self.registered_ids) < (ident-1):
            raise KeyError("unknown handler id #%d" % ident)

        handler = self.registered_ids[ident]
        if handler is None:
            raise Exception("handler #%d already unregistered" % ident)

        callback, event_type, predicate_args = handler
        self.registered[event_type].remove((callback, predicate_args))
        self.registered_ids[ident] = None


    
    def dispatch(self, event):
        #log.msg("dispatching %s event" % event.__class__.__name__)
        r = False
        for r_callback, r_args in self.get(event.__class__):
            
            o = event.consider(r_args)
            #log.msg("handler %s %s returned %d" % (str(r_callback), str(r_args), o))
            if o & ACCEPTED:
                r = True
                try:
                    r_callback(event)
                except Exception, ex:
                    self.error_handler(event=event, callback=r_callback, exception=ex)

                if o & FINISHED:
                    self.registered[event.__class__].remove((r_callback, r_args))
                if event.handled:
                    break
        return r
    
    def dispatch_delayed(self, event, delay):
        t = reactor.callLater(delay, lambda: self.dispatch(event))
        return t
    
    def dispatch_repeating(self, event, interval, now=False):
        t = task.LoopingCall(lambda: self.dispatch(event))
        t.start(interval, now)
        return t

    #get a list of handlers in the form (callback, {args...})
    def get(self, event_type):
        return self.registered.get(event_type, [])[::-1]


def get_timestamp(t=None):
    if t == None:
        return time.strftime("%Y-%m-%d %H:%M:%S")
    elif len(t) == 8:
        return time.strftime("%Y-%m-%d ") + t
    else:
        return t


#get an event type by name
def get_by_name(name):
    for n, c in get_all():
        if n.lower() == name.lower():
            return c


#get all events
def get_all():
    for n, c in inspect.getmembers(sys.modules[__name__], inspect.isclass):
        if issubclass(c, Event):
            yield n, c


def from_json(data):
    data = json.loads(data)
    return get_by_name(data['name'])(**data['data'])

from console import *
from error   import *
from hook    import *
from player  import *
from server  import *
from stat    import *
from user    import *
