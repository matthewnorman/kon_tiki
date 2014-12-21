from kontiki import raft, persist, rpc
from kontiki import persist
from twisted.trial import unittest
from twisted.internet import task
from kontiki.test.common import dropResult


def applyCommand(*args):
    return defer.succeed(None)

class DummyTask(object):

    def __init__(self):
        self.is_canceled = False

    def cancel(self, *args, **kwargs):
        self.is_canceled = True

    def active(self, *args, **kwargs):
        return True


class RaftStartsElectionTest(unittest.TestCase):

    def setUp(self):
        persister = persist.SQLitePersist(':memory:')
        persister.connect()
        identity = 'identity'
        peers = set()
        timeoutRange = (.150, .350)
        self.server = rpc.RaftServer(identity=identity, peers=peers,
                                     applyCommand=applyCommand,
                                     persister=persister)
        self.state = raft.StartsElection(identity=identity,
                                         server=self.server,
                                         peers=peers,
                                         applyCommand=applyCommand,
                                         electionTimeoutRange=timeoutRange,
                                         persister=persister)

        originalClock = raft.StartsElection.clock
        self.patch(raft.StartsElection, 'clock', task.Clock())

        def restoreClock():
            raft.StartsElection.clock = originalClock

        self.addCleanup(restoreClock)

    def test_cancel_all(self):
        dt = DummyTask()
        timeout = DummyTask()
        self.state.pending.add(dt)
        self.state.becomeCandidateTimeout = timeout
        self.state.cancelAll()
        self.assertTrue(dt.is_canceled)
        self.assertTrue(timeout.is_canceled)

    def test_timeout_loop(self):
        """
        Go through the whole thing and make sure that every time
        you go through the CandidateTimeout cycle that things end
        the right way.

        """

        self.assertIsNone(self.state.becomeCandidateTimeout)
        # This should do nothing
        self.state.cancelBecomeCandidateTimeout()
        self.assertIsNone(self.state.becomeCandidateTimeout)
        
