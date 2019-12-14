# ------------ Trabalho de Redes Digitais e Industriais ------------
# ---------------- Professor: Diego Stéfano (Dinho) ----------------
# ------------------------ Atividade: MyHDL ------------------------
# ----------------- Protocolo: CAN 2.0A - STANDART -----------------
# --------- Equipe: Laiana Rios, Robson Barbosa, Samuel Dias -------


# Simulação de uma comunicação entre dois nós utilizando comunicação serial
# A simulação consiste de um mestre enviando um pacote de 10 bits (7 de dados,
# 1 de paridade, 1 de start e 1 de stop) a um escravo
# O pacote é pré-codificado dentro do bloco mestre
# No escravo ele é armazenado dentro de uma lista, bit a bit, à medida que é recebido

from myhdl import block, delay, always, now, Signal

from fGeral import *

# Bloco Escravo: define estrutura do bloco que receberá o pacote do mestre
# Recebe dois sinais:
# "clock": necessário para a simulaçao funcionar
# "dados": onde o escravo vai ler os bits enviados pelo mestre

@block
def Escravo(clock, dados):
    # Este bloco contém propriedades, variáveis que guardam informações sobre o bloco
    # As propriedades podem ser alteráveis ou constantes
    # Foram aplicados a estrutura de dados dicionário de Python para representar os estados
    
    # constantes: dicionário que contém estados que não mudam ao longo da execução.
    constantes = {
        'tamanho_quadro': 127
    }

    # estado: dicionário que contém estados que podem mudar durante a execução
    estado = {
        # Item do dicionário que descreve o estado do barramento
        'barramento_inativo': True,   
        # Item do dicionário que descreve quantos bits foram recebidos
        'contagem_bits': 0,          
        
        'SOF':'', #BIT[0]
        'ARBITRATION':'',#BIT[1:11]
        'CONTROL':'',#BIT[12:17]
        

        'DATA':'',#BIT[18:-25]*
        #CRC len() = 16
        'CRC':'',#BIT[-25:-9]*

        'ACK':'',#BIT[-9:-7]
        'EOF':'',#BIT[-7:]
    }


    # quadro: lista onde serão armazenados os bits recebidos; o tamanho do quadro está armazenado no
    #         item "tamanho_quadro" do dicionário "constantes", e é acessado com a linha: constantes['tamanho_quadro']
    quadro = [0] * constantes['tamanho_quadro']
    
    # função "leitura": é chamada a cada subida do clock;
    # o seu funcionamento depende do status do barramento:
    # se o barramento estiver ativo então:
    # se a qtd de bits recebida é igual ao tamanho do quadro (ou seja, se a trasnmissão acabou) então:
    # faz o barramento inativo novamente
    # reseta a contagem de bits para 0 novamente
    # senão (ou seja, se a transimissão ainda não acabou):
    # o bit do quadro na posição igual ao contador de bits é igual ao bit presente no sinal "dados"
    # e soma um à contagem de bits
    # se o barramento estiver inativo e o sinal "dados" tiver valor 1 (ou seja, não comunicação no barramente e o escravo recebe o start bit do quadro):
    # muda o estado do barramento para ativo
    # e guarda o start bit na primeira posição do quadro (porque a contagem de bits está em zero).
    
    @always(clock.posedge)
    def leitura():
        if not estado['barramento_inativo']:
            if estado['contagem_bits'] == constantes['tamanho_quadro']:
                estado['barramento_inativo'] = True
                estado['contagem_bits'] = 0
                
                for x in range(126,0,-1):
                    if quadro[x] != '1':
                        quadro.pop(x)
                    else:
                        break

                estado['SOF'] = quadro[0]
                estado['ARBITRATION'] = quadro[1:13]
                estado['CONTROL'] = quadro[13:19]

                estado['DATA'] = quadro[19:-25]
                estado['CRC'] = quadro[-25:-9]

                estado['ACK'] = quadro[-9:-7]
                estado['EOF'] = quadro[-7:]

                print(estado)

                # Remove o encapsulamento da mensagem
                msg = estado['DATA']+estado['CRC']

                # Analisa a paridade -> Retira o bit inserido
                msg = paridadesOFF(''.join(str(e) for e in msg))

                # Chave do CRC
                key = "1100010110011001"

                # Converte do binário de máquina para uma string
                ans = decodeData(msg, key)
                print("RESTANTE APÓS A DECODIFICAÇÃO: " + ans)
                
                # Realiza a verificação de erro - CRC

                # Contabiliza quantos zeros precisa ter na resposta
                temp = "0" * (len(key) - 1)
                
                # Se o ans for igual ao temp, printa a resposta verdadeira
                if ans == temp:
                    print("THANKS. DADOS: <SAIDA>" + msg + "</SAIDA> NENHUM ERRO ENCONTRADO")
                    
                    # Manda o resultado para o cliente
                    print("OBRIGADA POR CONECTAR -> NENHUM ERRO ENCONTRADO")
                
                else:
                    print("ERRO NOS DADOS")
                    
                    # Manda o resultado para o cliente
                    print("OBRIGADA POR CONECTAR -> ERRO NOS DADOS")

            else:
                #print("DADOS ", estado['contagem_bits']," leitura", (dados))
                quadro[estado['contagem_bits']] = str(dados)
                estado['contagem_bits'] += 1
        elif dados == 1:
            print("Ativou o barramento")
            estado['barramento_inativo'] = False

            #quadro[estado['contagem_bits']] = str(dados)
            #estado['contagem_bits'] += 1

    # Todo bloco sempre retorna as funções (e somente as funções) definidas dentro dele.
    return leitura

# Bloco Mestre: define estrutura do bloco que enviará o pacote para o escravo
# Recebe dois sinais:
# "clock": necessário para a simulaçao funcionar.
# "dados": onde o mestre vai colocar os bits a serem enviados para o escravo.
@block
def Mestre(clock, dados):
    constantes = {
        'tamanho_quadro': 127
    }

    # O mestre manda no barramento, por isso ele pode assumir que o barramento está livre,
    # uma vez que apenas ele escreve no barramento.
    # Então o único estado variável que ele precisa manter é quantos bits já foram enviados.
    estado = {
        'contagem_bits': 0
    }
    
    # Teste de envio! 
    quadro = [1, 1, 0, 1, 1, 0, 1, 0, 0, 1]

    # Chamar o encode aqui
    msg = input("DIGITE A MENSAGEM EM BINARIO QUE VOCÊ DESEJA ENVIAR: ")

    print("MENSAGEM RECEBIDA:    ",msg)

    # Define o CRC
    key = "1100010110011001"

    # encodeData = Codificação da mensagem
    ans = encodeData(msg, key)

    print("MENSAGEM COM CRC:    ",ans)

    # Entra com o verificador de segurança!
    ans = paridadesIN(ans)

    print("MENSAGEM COM PARIDADE:    ",ans)

    # Faz o encapsulamento da mensagem
    
    # Ativa o barramento manualmente...
    ativador= "1" 

    encap = "0100110001000001000" #len = 19
    encap2 = "011111111" #len = 9

    ans = str(ativador) + str(encap) + ans + str(encap2)
    
    print("MENSAGEM ENCAPSULADA E ENVIADA:    ",ans)

    quadro = list(map(int, str(ans)))

    print("Tamanho da mensagem: ",len(quadro))

    # Função "escrita": é chamada a cada subida do clock;
    # Pseudocódigo de funcionamento:
    # Se o contador de bits enviados for menor que o tamanho do quadro (ou seja, ainda há bits a enviar) então:
    # Põe o próximo bit no sinal dados e incremente contador de bits, senão (ou seja, se todos os bits já foram enviados):
    # Coloca o barramento em nível inativo, que é o bit 0
    
    @always(clock.posedge)
    def escrita():
        # TODO TAMANHO DO QUADRO VARIAVEL, NECESSIDADE DE ADAPTAÇÃO DO CODIGO
        if estado['contagem_bits'] < constantes['tamanho_quadro'] and estado['contagem_bits'] < len(quadro):
            #print("BIT ",estado['contagem_bits']," ENVIADO", quadro[estado['contagem_bits']])
            dados.next = quadro[estado['contagem_bits']]
            estado['contagem_bits'] += 1
        else:
            dados.next = 0

    return escrita

# Block Top: bloco que cria e conecta os nós.
@block
def Top():
    # Criação do sinal de clock que vai atuar nos nós
    clock_global = Signal(0) 
    # Criação do sinal que representa o barramento
    dados = Signal(0) 
    dados2 = Signal(1)

    # Criação de um escravo conectado ao clock e ao barramento
    escravo = Escravo(clock_global, dados) 
    # Criação de um escravo conectado ao clock e ao barramento
    escravo2 = Escravo(clock_global, dados2) 
    
    # Criação de um mestre conectado ao clock e ao barramento
    mestre = Mestre(clock_global, dados) 
    # Criação de um mestre conectado ao clock e ao barramento
    mestre2 = Mestre(clock_global, dados2) 
    
    # Função que gera sinal de clock alternando o nível lógico do sinal "clock_global" a cada 10ns
    @always(delay(10))
    def clock():
        clock_global.next = not clock_global

    # Retorna funções criadas dentro do bloco Top.
    return clock, escravo, escravo2, mestre, mestre2


# Até agora, apenas estruturas de blocos foram definidas. Chegou a hora de criar instâncias e executá-las.
# Abaixo, "inst" é uma instância do bloco Top.
inst = Top()

# Executar a simulação para 500ns.
inst.run_sim(5000)
