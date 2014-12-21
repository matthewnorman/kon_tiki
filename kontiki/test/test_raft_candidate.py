from kontiki import raft, rpc
from kontiki import persist
from twisted.trial import unittest
from twisted.internet import task
from kontiki.test.common import dropResult


def applyCommand(*args):
    return defer.succeed(None)


class RaftCandidateTest(unittest.TestCase):

    def setUp(self):
        persister = persist.SQLitePersist(':memory:')
        persister.connect()
        identity = 'identity'
        peers = set()
        timeoutRange = (.150, .350)
        self.server = rpc.RaftServer(identity=identity, peers=peers,
                                     applyCommand=applyCommand,
                                     persister=persister)
        self.state = raft.Candidate(identity=identity,
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

    def test_willBecomeLeader_False(self):
        self.state.peers = set([1, 2])
        results = self.state.willBecomeLeader(votesSoFar=0)
        msg = 'Should be false with 0 votes'
        results.addCallback(self.assertFalse, msg=msg)
        results.addCallback(dropResult(self.assertTrue,
                                       isinstance(self.server.state,
                                                  raft.Follower)))
        return results

    def test_willBecomeLeader_True(self):
        self.state.peers = set([1, 2])
        results = self.state.willBecomeLeader(votesSoFar=2)
        msg = 'Should be true with 2 votes'
        results.addCallback(self.assertFalse, msg=msg)
        results.addCallback(dropResult(self.assertTrue,
                                       isinstance(self.server.state,
                                                  raft.Leader)))
        return results
