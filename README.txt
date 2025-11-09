# Atividade 2 — Mineração de Criptomoedas com gRPC (Python)
NOME: IAN VINICIUS VIDELA JACÓ - 2213648

## Disciplina
Programação Distribuída e Paralela


## Tema
Implementação de um protótipo de **minerador de criptomoedas** utilizando **Python e gRPC**, seguindo o modelo **Cliente/Servidor** e o conceito de **Chamada de Procedimento Remoto (RPC)**.

---

## Objetivo
Esta atividade tem como objetivo aplicar o conceito de **RPC (Remote Procedure Call)** por meio da tecnologia **gRPC**, desenvolvendo uma aplicação distribuída onde o servidor gerencia desafios criptográficos e os clientes (mineradores) competem para resolvê-los.

A aplicação simula o funcionamento de um sistema de **mineração de criptomoedas**, no qual:
- O **servidor** gera desafios (hashes SHA-1 com diferentes níveis de dificuldade);
- Os **clientes** tentam encontrar uma string (“solução”) que satisfaça o desafio;
- O primeiro cliente que resolver o desafio é declarado **vencedor** e um novo desafio é criado automaticamente.

---

## Estrutura de Arquivos
PROJETO2/
│
├── miner.proto # Definição da interface RPC (serviços e mensagens)
├── miner_pb2.py # Arquivo gerado automaticamente pelo gRPC
├── miner_pb2_grpc.py # Arquivo auxiliar gerado automaticamente pelo gRPC
├── server_miner.py # Implementação do servidor RPC
├── miner_client.py # Implementação do cliente minerador
└── README.md # Documento técnico com explicações e instruções

---

## Tecnologias Utilizadas
- **Linguagem:** Python 3.10+
- **Bibliotecas:** `grpcio`, `grpcio-tools`, `hashlib`, `threading`
- **Protocolo:** gRPC sobre HTTP/2
- **Serialização:** Protocol Buffers (Protobuf)
- **Modelo:** Cliente/Servidor (RPC)

---

## Metodologia de Implementação

### 1. Arquivo `.proto`
Define a interface RPC utilizada para comunicação entre cliente e servidor.  
Contém os serviços:
- `getTransactionID()`
- `getChallenge(transactionID)`
- `getTransactionStatus(transactionID)`
- `getWinner(transactionID)`
- `getSolution(transactionID)`
- `submitChallenge(transactionID, clientID, solution)`

### 2. Servidor (`server_miner.py`)
- Mantém uma tabela com as transações ativas:
TransactionID | Challenge | Solution | Winner


- Cada **Challenge** representa o nível de dificuldade (1 a 20).
- Um desafio é considerado resolvido quando a função `SHA-1(solution)` começa com `N` zeros hexadecimais, onde `N` é o valor do desafio.
- Após um cliente vencer, o servidor registra o vencedor e cria automaticamente um novo desafio.

### 3. Cliente (`miner_client.py`)
- Recebe o endereço do servidor via argumento (`--server`).
- Permite interação por menu:
1 - getTransactionID
2 - getChallenge
3 - getTransactionStatus
4 - getWinner
5 - getSolution
6 - Mine
0 - Sair

- A opção **Mine** realiza os passos:
1. Solicita a transação atual ao servidor;
2. Obtém o desafio associado;
3. Tenta encontrar uma solução localmente (brute-force);
4. Submete ao servidor para validação;
5. Mostra o resultado e o vencedor.

- A mineração local utiliza **várias threads** (definidas com o argumento `--threads`), acelerando a busca por uma solução.

---




## Instruções de Execução

### 1. Instalar as dependências

pip install grpcio grpcio-tools

2. Gerar os arquivos gRPC (caso ainda não existam)


python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. miner.proto

3. Executar o servidor

python server_miner.py
Saída esperada:


[NEW TX] txid=0, challenge=3
Servidor Miner inicializado com txid 0.
Servidor Miner rodando na porta 50052...

4. Executar o cliente

Em outro terminal:

python miner_client.py --client-id 1

5. No menu do cliente
Escolha 6 (Mine) para iniciar a mineração.

Quando encontrar uma solução válida, o cliente exibirá:


Solução encontrada localmente: 1-0-123456
Resposta do servidor: 1 - válida
O servidor exibirá:


[SOLVED] txid=0 by client=1
[NEW TX] txid=1, challenge=4

Testes e Resultados

Testes foram realizados com diferentes níveis de desafio (1–6).

Clientes concorrentes (ClientID=1 e ClientID=2) conseguiram disputar o mesmo desafio simultaneamente.

O servidor registrou corretamente o vencedor e gerou novas transações automaticamente.

O uso de múltiplas threads reduziu significativamente o tempo de mineração local.

Para desafios baixos (1–4), o tempo médio de solução ficou abaixo de 5 segundos.



Observações:
O servidor mantém consistência de dados com locks para evitar condições de corrida.

Cada cliente envia strings no formato "ClientID-TxID-Nonce" para gerar valores únicos.

O protocolo gRPC garante a entrega das mensagens e a integridade das respostas.

A regra de validação pode ser facilmente ajustada na função _check_solution() do servidor.

CONCLUSÃO

O projeto demonstra, de forma prática, como sistemas distribuídos podem empregar RPC para coordenar tarefas complexas entre múltiplos processos.
O uso do gRPC simplificou a implementação das chamadas remotas, enquanto o SHA-1 e o controle de dificuldade simularam adequadamente o comportamento de mineração.

A aplicação atende integralmente os requisitos:

Comunicação Cliente/Servidor via RPC;

Persistência e gerenciamento de transações;

Paralelismo local no cliente;

Atualização automática de desafios;

Resultados reproduzíveis e validados pelo servidor.