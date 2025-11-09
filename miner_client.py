# miner_client.py
import grpc
import argparse
import threading
import time
import random
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

import miner_pb2
import miner_pb2_grpc

DEFAULT_PORT = 50052

def sha1_hex(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()

class MinerClient:
    def __init__(self, server_addr, client_id, threads=4):
        self.channel = grpc.insecure_channel(server_addr)
        self.stub = miner_pb2_grpc.MinerStub(self.channel)
        self.client_id = client_id
        self.threads = threads

    def menu(self):
        while True:
            print("\n=== Miner Client ===")
            print("1 - getTransactionID")
            print("2 - getChallenge")
            print("3 - getTransactionStatus")
            print("4 - getWinner")
            print("5 - getSolution")
            print("6 - Mine")
            print("0 - Sair")
            choice = input("Escolha: ").strip()
            if choice == '0':
                break
            if choice == '1':
                self._do_getTransactionID()
            elif choice == '2':
                self._do_getChallenge()
            elif choice == '3':
                self._do_getTransactionStatus()
            elif choice == '4':
                self._do_getWinner()
            elif choice == '5':
                self._do_getSolution()
            elif choice == '6':
                self._do_mine()
            else:
                print("Opção inválida.")

    def _do_getTransactionID(self):
        r = self.stub.getTransactionID(miner_pb2.Empty())
        print("Current txid:", r.value)

    def _ask_txid_input(self):
        try:
            txid = int(input("transactionID: ").strip())
            return txid
        except ValueError:
            print("transactionID inválido.")
            return None

    def _do_getChallenge(self):
        txid = self._ask_txid_input()
        if txid is None: return
        r = self.stub.getChallenge(miner_pb2.TxRequest(txid=txid))
        print("Challenge:", r.challenge)

    def _do_getTransactionStatus(self):
        txid = self._ask_txid_input()
        if txid is None: return
        r = self.stub.getTransactionStatus(miner_pb2.TxRequest(txid=txid))
        print("Status ( -1 invalid, 0 solved, 1 pending ): ", r.status)

    def _do_getWinner(self):
        txid = self._ask_txid_input()
        if txid is None: return
        r = self.stub.getWinner(miner_pb2.TxRequest(txid=txid))
        print("Winner ( -1 invalid, 0 none, >0 client id ): ", r.winner)

    def _do_getSolution(self):
        txid = self._ask_txid_input()
        if txid is None: return
        r = self.stub.getSolution(miner_pb2.TxRequest(txid=txid))
        print(f"Status: {r.status}, Challenge: {r.challenge}, Solution: '{r.solution}'")

    def _mine_worker(self, txid, challenge, stop_event, start_nonce):
        nonce = start_nonce
        while not stop_event.is_set():
            candidate = f"{self.client_id}-{txid}-{nonce}"
            h = sha1_hex(candidate)
            if h.startswith('0' * challenge):
                return candidate  # found
            nonce += 1
        return None

    def _do_mine(self):
        # 1) get txid
        r = self.stub.getTransactionID(miner_pb2.Empty())
        txid = r.value
        print("Mining txid:", txid)

        # 2) get challenge
        ch_r = self.stub.getChallenge(miner_pb2.TxRequest(txid=txid))
        challenge = ch_r.challenge
        if challenge <= 0:
            print("Transaction inválida ou challenge inválido:", challenge)
            return
        print("Challenge (difficulty):", challenge)

        # 3) local search (multi-thread)
        stop_event = threading.Event()
        found_solution = None

        print(f"Iniciando mineração com {self.threads} threads... (pode demorar dependendo do challenge)")
        with ThreadPoolExecutor(max_workers=self.threads) as ex:
            # start several workers with staggered nonces
            futures = []
            for i in range(self.threads):
                start_nonce = random.randint(0, 1000000) + i * 100000
                futures.append(ex.submit(self._mine_worker, txid, challenge, stop_event, start_nonce))

            for fut in as_completed(futures):
                sol = fut.result()
                if sol:
                    found_solution = sol
                    stop_event.set()
                    break

        if not found_solution:
            print("Nenhuma solução encontrada (threads encerradas).")
            return

        # 4) imprimir localmente a solução
        print("Solução encontrada localmente:", found_solution)
        # 5) submeter
        submit_req = miner_pb2.SubmitRequest(txid=txid, client_id=self.client_id, solution=found_solution)
        resp = self.stub.submitChallenge(submit_req)
        # 6) imprimir resposta do servidor
        resmap = {1: "válida (você venceu!)", 0: "inválida", 2: "já solucionado por outro", -1: "txid inválida"}
        print("Resposta do servidor:", resp.result, "-", resmap.get(resp.result, "desconhecido"))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--server', default=f'localhost:{DEFAULT_PORT}', help='server address host:port')
    parser.add_argument('--client-id', type=int, required=True, help='Client ID (inteiro)')
    parser.add_argument('--threads', type=int, default=4, help='número de threads para mineração local')
    args = parser.parse_args()

    mc = MinerClient(args.server, args.client_id, threads=args.threads)
    mc.menu()

if __name__ == "__main__":
    main()
