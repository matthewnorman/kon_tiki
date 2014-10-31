from kon_tiki import raft
from kon_tiki import persist
from twisted.trial import unittest


class RaftServerTest(unittest.TestCase):

    def create_server(self):
        persister = persist.ListPersist()
        identity = 'identity'
        peers = set()
        applyCommand = None
        timeoutRange = (.150, .350)
        cycle = raft.ServerCycle(identity=identity, peers=peers,
                                 applyCommand=applyCommand,
                                 persister=persister)
        server = raft.Server(identity=identity, cycle=cycle,
                             peers=peers, applyCommand=applyCommand,
                             electionTimeoutRange=timeoutRange,
                             persister=persister)
        return server

    def test_candidateIdOK(self):
        """
        CandidateIdOK should check whether or not we voted
        for another candidate.
        """
        server = self.create_server()
        ID = 'some_ID'
        self.assertTrue(server.candidateIdOK(candidateId=ID))
        server.persister.votedFor = 'other_ID'
        self.assertFalse(server.candidateIdOK(candidateId=ID))
        server.persister.votedFor = 'some_ID'
        self.assertTrue(server.candidateIdOK(candidateId=ID))


    def test_candidateLogUpToDate(self):
        """
        Is the candidate up to date? The term and the index together
        have to be at least as advanced as that of the current machine.

        """

        server = self.create_server()
        currentTerm = 100
        log = []
        for x in xrange(10):
            log.append(persist.LogEntry(term=currentTerm, command=x))

        server.persister.currentTerm = currentTerm
        server.persister.log = log
        print server.candidateLogUpToDate(lastLogIndex=len(log),
                                          lastLogTerm=currentTerm)


    def test_requestVote(self):
        """
        Do I give you a vote? It depends.

        1) Is your term less than mine? If so, the answer is no.
        2) Have I voted for you before, and candidate log is up to date
        """
        server = self.create_server()

        currentTerm = 100
        candidateId = 'ThisCandidate'
        lastLogIndex = 10
        lastLogTerm = 100

        # Test for term
        server.persister.currentTerm = 101
        term, vg = server.remote_requestVote(term=currentTerm,
                                             candidateId=candidateId,
                                             lastLogIndex=lastLogIndex,
                                             lastLogTerm=lastLogTerm)
        self.assertEquals(term, 101)
        self.assertFalse(vg)

        
