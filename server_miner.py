# server_miner.py
import grpc
from concurrent import futures
import time
import threading
import random
import hashlib

import miner_pb2
import miner_pb2_grpc

# Parâmetros
PORT = 50052  # porta do serviço miner (mude se necessário)
MAX_WORKERS = 10

class MinerServer(miner_pb2_grpc.MinerServicer):
    def __init__(self):
        # transactions: txid -> dict {Challenge:int, Solution:str, Winner:int, Solved:bool}
        self.lock = threading.Lock()
        self.transactions = {}
        self.max_txid = -1
        # ao iniciar, geramos txid = 0
        self._new_transaction(0)
        print("Servidor Miner inicializado com txid 0.")

    def _new_transaction(self, txid=None):
        with self.lock:
            if txid is None:
                txid = self.max_txid + 1
            challenge = random.randint(1, 4)
            self.transactions[txid] = {
                "Challenge": challenge,
                "Solution": "",
                "Winner": -1,
                "Solved": False,
                "created_at": time.time()
            }
            self.max_txid = max(self.max_txid, txid)
            print(f"[NEW TX] txid={txid}, challenge={challenge}")
            return txid

    # requisito de validação: sha1(solution) começa com C zeros hex
    @staticmethod
    def _check_solution(challenge, solution):
        h = hashlib.sha1(solution.encode('utf-8')).hexdigest()
        prefix = '0' * challenge
        return h.startswith(prefix)

    # RPCs
    def getTransactionID(self, request, context):
        with self.lock:
            # retorna o menor txid pendente (Winner == -1)
            for txid in sorted(self.transactions.keys()):
                if not self.transactions[txid]["Solved"]:
                    return miner_pb2.IntReply(value=txid)
            # se todos resolvidos, cria nova tx
            new_tx = self._new_transaction()
            return miner_pb2.IntReply(value=new_tx)

    def getChallenge(self, request, context):
        txid = request.txid
        with self.lock:
            if txid not in self.transactions:
                return miner_pb2.ChallengeReply(challenge=-1)
            return miner_pb2.ChallengeReply(challenge=self.transactions[txid]["Challenge"])

    def getTransactionStatus(self, request, context):
        txid = request.txid
        with self.lock:
            if txid not in self.transactions:
                return miner_pb2.StatusReply(status=-1)
            return miner_pb2.StatusReply(status=0 if self.transactions[txid]["Solved"] else 1)

    def submitChallenge(self, request, context):
        txid = request.txid
        client_id = request.client_id
        solution = request.solution
        with self.lock:
            if txid not in self.transactions:
                return miner_pb2.SubmitReply(result=-1)
            if self.transactions[txid]["Solved"]:
                return miner_pb2.SubmitReply(result=2)
            # validar
            challenge = self.transactions[txid]["Challenge"]
            valid = self._check_solution(challenge, solution)
            if valid:
                self.transactions[txid]["Solution"] = solution
                self.transactions[txid]["Winner"] = client_id
                self.transactions[txid]["Solved"] = True
                print(f"[SOLVED] txid={txid} by client={client_id}")
                # cria nova transação automaticamente
                self._new_transaction()
                return miner_pb2.SubmitReply(result=1)
            else:
                return miner_pb2.SubmitReply(result=0)

    def getWinner(self, request, context):
        txid = request.txid
        with self.lock:
            if txid not in self.transactions:
                return miner_pb2.WinnerReply(winner=-1)
            winner = self.transactions[txid]["Winner"]
            return miner_pb2.WinnerReply(winner=(0 if winner == -1 else winner))

    def getSolution(self, request, context):
        txid = request.txid
        with self.lock:
            if txid not in self.transactions:
                return miner_pb2.SolutionInfo(status=-1, solution="", challenge=-1)
            rec = self.transactions[txid]
            status = 0 if rec["Solved"] else 1
            sol = rec["Solution"]
            ch = rec["Challenge"]
            return miner_pb2.SolutionInfo(status=status, solution=sol, challenge=ch)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=MAX_WORKERS))
    miner_pb2_grpc.add_MinerServicer_to_server(MinerServer(), server)
    server.add_insecure_port(f'[::]:{PORT}')
    server.start()
    print(f"Servidor Miner rodando na porta {PORT}...")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("Servidor interrompido (Ctrl+C).")

if __name__ == "__main__":
    serve()
