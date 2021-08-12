"""
THIS SCRIPT IS MEANT TO BE IMPORTED TO BE ABLE TO 
IMPLEMENT THE OBSERVER PATTERN
"""

class Observable():
    """
    This class is meant to be an observable, 
    will notify any observers when notify is called
    """

    def __init__(self):
        self.targets = set()

    def watched_by(self, observer):
        self.targets.add(observer)

    def unwatched_by(self, observer):
        self.targets.remove(observer)

    def notify(self, arglist=[]):
        for target in self.targets:
            target.act(arglist)

class Observer():
    """
    This class is meant is meant to observe, 
    and when it is notified will act
    """

    def __init__(self):
        self.watching = set()

    def act(self, arglist):
        pass
