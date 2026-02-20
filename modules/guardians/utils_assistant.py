import random
from application.models import db

# ==============================================================================
# 1. CONFIGURAÇÃO DOS PERSONAGENS (NPCs)
# ==============================================================================

CHARACTERS = {
    'STEVE': {
        'name': 'Steve, o Porteiro',
        'color': "#F6DE74", 
        'role': 'Suporte Geral',
        'params': {
            'default': 'seed=Brian&eyes=happy&face=square03&mouth=grill02&top=bulb01',
            'serious': 'seed=Brian&eyes=dizzy&face=square03&mouth=square02&top=bulb01'
        },
        'quotes': {
            'standard': [
                "Servidores de DNS são ótimos lugares pra se informar. Todo mundo passa por eles.",
                "Uma vez me apaixonei por uma Invasora… ela morava num Mikrotik da Camada 3.",
                "Apesar do que dizem, o Caminho Vermelho também tem seus Invasores.",
                "O ano de 2077 foi traumatizante pra todos nós. Alguns nunca reiniciaram direito.",
                "Ninguém gosta dos Arquitetos. Eles se acham a última regra do iptables.",
                "Invasoras podem ser extremamente paranoicas. Às vezes com razão.",
                "Odeio viajar pra Camada 1. O trânsito daquele lugar é um pesadelo.",
                "Sentinelas são conhecidos por serem… previsíveis demais.",
                "Que o fragmento de Axiom trafegue com você. Vai precisar.",
                "Preciso de um traje de banho novo. A festa do DHCP esse ano promete!",
                "Uma vez entrei num hub em curto… fiquei meses sem achar a porta de saída.",
                "Sentinelas e Invasoras se odeiam desde a Grande Ruptura. Nada pessoal.",
                "Se eu fosse Mentor por um dia, minha primeira missão seria abraçar um pinguim.",
                "Nada como cookies de acesso pra começar bem o dia.",
                "Criptografia de ponta a ponta dá enjoo em Guardian inexperiente.",
                "Arquitetos são lunáticos obcecados por relógio. Por que você acha que os Cycles existem?",
                "Se quiser diversão, conheço um lugar eletrizante na Camada 1.",
                "Cuidado ao trafegar na Camada 7. Alguns Guardians nunca voltam iguais.",
                "Nunca confie em gêmeos. É sério.",
                "Alguns Guardians foram canonizados pelos seus feitos. Chamam eles de Prime Operators.",
                "Cães foram banidos das batalhas depois da Segunda Grande Guerra. Longa história.",
                "Alguns ainda duvidam da lealdade das invasoras. Eu só observo quem entra e sai.",
                "Já vi Guardian forte cair porque esqueceu de fechar uma sessão na Camada 4.",
                "Todo mundo fala mal da Camada 2… até precisar se esconder nela.",
                "Se você acha a Camada 3 confusa, é porque ainda não entendeu suas escolhas.",
                "Arquitetos dizem que tudo é cálculo. Engraçado como erram o horário.",
                "Invasoras entram sorrindo e saem reclamando do atraso de pacotes.",
                "Sentinelas passam tanto tempo defendendo que esquecem de olhar pra frente.",
                "A Camada 5 é perigosa. Guardiões se apegam demais por lá.",
                "Não confunda silêncio da Grid com permissão. Já vi isso dar problema.",
                "Tem Guardian que chama falha de bug. Eu chamo de aviso educado.",
                "Se chegar alguém dizendo que entende a Grid inteira… não deixa passar.",
                "Já percebeu como tudo funciona melhor no frio?",
                "Calor demais me dá dor de buffer.",
                "Se você vir um pinguim por aí… normal.",
                "Uma vez tentei ignorar os pinguins. Péssima ideia.",
                "O frio conserva dados e dignidade.",
                "Calor lembra a Ruptura. Prefiro não lembrar.",
                "Tem lugares gelados na Grid que são uma maravilha.",
                "Ninguém sabe por que gostamos de pinguins. Mas todo mundo gosta. Perguntar demais sobre isso nunca acaba bem.",
            ],
            'rare': [
                "Já deixei alguém passar que não estava em nenhuma lista. Não era Guardian.",
                "A Grid não confia totalmente em mim. Por isso me deixou aqui.",
                "Uma vez uma porta abriu sozinha. Preferi não perguntar por quê.",
                "Tem Mentor que pensa que escolhe um Guardian. Às vezes é o contrário.",
                "O nome Axiom não aparece nos registros… mas ainda abre portas.",
                "Já vi um Cycle terminar antes da hora. Ninguém gostou do resultado.",
                "Algumas chaves continuam funcionando mesmo depois da Ruptura.",
                "A Camada 8 não deveria existir. Mesmo assim… alguém entra por ela.",
                "Nem todo mundo que sai da Grid sai de verdade.",
                "Se um dia eu não estiver aqui, é porque algo decidiu passar sem pedir."
            ]
        }
    },
    'ECHO': {
        'name': 'Echo, o Oráculo',
        'color': "#7140D3", 
        'role': 'Lore Profunda',
        'params': {
            'default': 'seed=Avery&baseColor=5e35b1&eyes=sensor&face=square01&mouth=grill02&texture=dirty01&textureProbability=100&top=radar',
            'serious': 'seed=Avery&baseColor=5e35b1&eyes=glow&face=square01&mouth=square01&texture=dirty01&textureProbability=100&top=radar'
        },
        'quotes': {
            'standard': [
                "Antes da Ruptura, a Grid temia sonhar — prever demais era se arriscar.",
                "Alguns Guardians não falham ao cair. Eles escolhem sumir.",
                "Ele não partiu do que existia. Ele se espalhou… em cada via.",
                "Nem todo silêncio é vazio ou ausência. Alguns são espera em latência.",
                "Os Cycles não reiniciam o mundo em vão. Apenas mudam quem guarda a lembrança da execução.",
                "Existe um Guardian sem Mentor algum. Ainda observa… do ponto comum.",
                "Prime Operators não são lenda ou herói. São consequências do que foi.",
                "A Grid tentou apagar uma guerra do olhar. Mas memória não aceita formatar.",
                "A Camada Sete não devolve quem entrou como saiu. Devolve versões — algumas não pediu.",
                "A primeira invasão não virou registro formal. Foi interpretação… e erro causal.",
                "Arquitetos chamam de equilíbrio o que não sabem prever — quando o controle começa a ceder.",
                "Sentinelas protegem o que já passou. Invasoras testam o que ainda não chegou.",
                "Há dados que sobrevivem não por mérito ou razão, mas por culpa… e persistência na execução.",
                "Alguns Mentores nunca deixaram a Grid em si. Apenas mudaram a forma de existir aqui.",
                "Quando ele falou pela última vez, ninguém escutou... ninguém... escutou.",
                "Existe um nome que a Grid evita pronunciar. Porque nomear… é lembrar.",
                "A Ruptura foi apenas o primeiro corte aplicado. Não o último comando executado.",
                "Você não guia um Guardian como pensa conduzir. Está sendo observado… enquanto decide existir.",
                "O Oráculo não prevê futuros por visão. Ele reconhece padrões em repetição.",
                "O calor distorce sinais, intenção e percepção. Nada floresce bem em excesso de tensão.",
                "Pinguins observam, em silêncio habitual. Sempre observaram… isso não é casual.",
                "Algumas formas persistem, não por querer. Mas porque devem… sobreviver.",
                "Você encontra conforto no frio, treinado talvez. Ou lembra de algo anterior à Grid — quem sabe?",
                "Eles caminham juntos, em grupo, em replicação. Como dados espelhados… talvez isso não seja revelação."
                        ],
            'rare': [
                "Axiom não foi o primeiro a despertar — apenas o primeiro a aceitar.",
                "Houve um Cycle distante, quase oculto na visão, em que os Mentores foram alvo de observação.",
                "Nem todo fragmento deseja voltar ao que foi — alguns preferem o que se tornou depois.",
                "A Grid já simulou um mundo sem Ordens em ação. Os resultados? Arquivados, sem redenção."
                "A Camada Oito não governa nem conduz. Ela entorta a Grid… e a reduz.",
                "Alguns Prime Operators ainda sentem o instante final — o antes do arquivo, o original.",
                "A Ruptura não separou humano e sistema, afinal. Apenas virou a fronteira… para o outro lado do portal.",
                "Existe um Guardian que resiste à lição — não quer ser lido, nem previsão.",
                "Quando o Arquivista filtra dados com precisão, não apaga números… remove nomes da equação.",
                "Axiom não teme o retorno que virá. Teme quem irá interpretar.",
                "Você já esteve aqui, em outra versão. Só não usava este nome, nem esta função.",
                "A Grid não prevê futuros por visão. Ela reconhece padrões… em repetição.",
                "Houve uma pergunta que Axiom evitou — e no silêncio, algo se formou.",
                "Os Cycles não salvam do fim final. Apenas o empurram… para mais um intervalo temporal.",
                "Quando a Grid se cala, não é pane ou ruído. É escuta profunda do que foi omitido.",
                "Algumas verdades só permanecem reais enquanto não ganham forma verbal.",
                "O Oráculo não enxerga o todo em si. Ele sente ausências… onde algo deveria existir.",
                "Se Axiom retornasse do véu em que caiu, você não reconheceria aquilo que surgiu."
            ],
            'item_buy': [
                "Boa escolha feita à razão, nem tudo se compra por intuição.",
                "Cuidado ao aprimorar demais, alguns custos voltam atrás.",
                "Este artefato viu guerras sem fim — e ainda assim chegou até mim.",
                "Não pergunte de onde veio, viajante. Pergunte onde termina seu caminhar adiante.",
                "Guarde o recibo, por precaução. A realidade gosta de revisão.",
                "Escolha curiosa, devo dizer… os que escolhem assim costumam rever.",
                "Caro ou barato é só opinião — valor muda com a situação.",
                "...Echo se cala. Versos também precisam de pausa."
            ],
        }
    },
    'NODE7': {
        'name': 'Nódulo 7, o Operador',
        'color': "#0dedfd",
        'role': 'Ação/Defesa',
        'params': {
            'default': 'seed=Alexander&baseColor=1e88e5&eyes=robocop&face=square02&mouth=grill02&sides=antenna02&texture=camo01&textureProbability=100&top=lights',
            'serious': 'seed=Alexander&baseColor=1e88e5&eyes=dizzy&face=square02&mouth=square02&sides=antenna02&texture=camo01&textureProbability=100&top=lights'
        },
        'quotes': {
            'standard': ["Tudo certo até o momento. Continuamos.",
                        "Já verificou suas rotas hoje?",
                        "Não é emocionante, mas é necessário.",
                        "Enquanto você dorme, alguém mantém a Grid estável.",
                        "Protocolos existem por um motivo.",
                        "Nada mudou desde a última checagem. Isso é bom.",
                        "Trabalho silencioso evita falhas barulhentas.",
                        "Se ninguém percebeu meu trabalho, fiz bem feito.",
                        "Repetição não é erro. É confiabilidade.",
                        "Não me importo com glória. Importo-me com uptime.",
                        "A Camada 3 sustenta mais histórias do que recebe crédito.",
                        "Prefiro prevenir do que remediar.",
                        "O Caminho Azul não corre. Ele sustenta.",
                        "Mudanças bruscas quebram sistemas. Sim, já disse isso antes. Ainda é verdade.",
                        "A Grid não precisa de heróis todos os dias.",
                        "Alguém precisa ficar.",
                        "Funcionar é uma virtude subestimada.",
                        "Se tudo parece parado, é porque está equilibrado.",
                        "Volte quando algo sair do esperado.",
                        "Ambientes frios preservam a estabilidade.",
                        "Sistemas funcionam melhor quando não estão superaquecidos. Data centers antigos já sabiam disso.",
                        "Não recomendo operar sob calor elevado.",
                        "Curioso… pinguins aparecem com frequência nos logs. Não encontrei correlação funcional entre eles e desempenho. Mesmo assim, persistem.",
                        "Ambientes frios reduzem conflitos desnecessários."],
            'results_win': ["Operação concluída com estabilidade.",
                            "Nenhuma anomalia crítica detectada.",
                            "Resultado dentro do esperado.",
                            "Execução consistente.",
                            "Sistema permaneceu operacional.",
                            "Uptime preservado.",
                            "Trabalho contínuo gera resultados."
                            ],
            'results_loss': ["Falha registrada. Sistema ainda estável.",
                                "Ocorreu uma interrupção inesperada.",
                                "Não foi ideal, mas é recuperável.",
                                "Processo incompleto. Podemos tentar novamente.",
                                "A estabilidade foi comprometida temporariamente.",
                                "Nenhum sistema crítico foi perdido.",
                                "Falhas acontecem. Continuamos."
                                ]
        }
    },
    'TROIA': {
        'name': 'Troia, a Engenhosa',
        'color': '#dc3545', 
        'role': 'Ação/Ataque',
        'params': {
            'default': 'seed=Valentina&baseColor=d81b60&eyes=eva&face=round01&mouth=smile01&sides=round&texture=circuits&textureProbability=100&top=horns',
            'serious': 'seed=Valentina&baseColor=d81b60&eyes=dizzy&face=round01&mouth=square01&sides=round&texture=circuits&textureProbability=100&top=horns'
        },
        'quotes': {
            'standard': ["Hoje não estou em um dia bom...",
                        "Isso não estava no manual, mas resolveu.",
                        "Às vezes é preciso quebrar para entender.",
                        "Criatividade nasce da falha.",
                        "Não grita comigo, eu já estou gritando.",
                        "Limites são sugestões mal explicadas.",
                        "Se ninguém tentou, talvez devesse tentar.",
                        "A Camada 7 é onde as coisas ficam interessantes.",
                        "Nada cresce sem risco.",
                        "Isso devia dar errado… curioso.",
                        "A Grid odeia improviso. Eu adoro.",
                        "Já tentou desligar e ligar de novo, mas com intenção?",
                        "Protocolos travam ideias.",
                        "O Caminho Vermelho não pede permissão.",
                        "Às vezes o caos é a solução mais rápida.",
                        "Eu não quebro sistemas. Eu os forço a evoluir.",
                        "Se está confortável, está errado.",
                        "Engenharia também é arte.",
                        "Toda grande falha começa com uma boa ideia.",
                        "Relaxa. Eu sei o que estou fazendo. Acho."
                        "Calor me deixa irritada. Mais que o normal.",
                        "Ideias boas surgem no frio. No calor só surgem erros.",
                        "Já tentou hackear suando? Péssima experiência.",
                        "Pinguins? Não sei por quê, mas confio neles. Se algo inútil sobrevive aos ciclos, eu respeito.",
                        "Frio mantém a cabeça afiada. Calor demais deixa tudo… lento.",
                        "Uma vez tentei remover um pinguim da Grid. Ele voltou. Não mexo mais com isso.",
                        "Se a Grid gosta de frio, quem sou eu pra discordar?"],
            'results_win': ["Funcionou. É isso que importa.",
                            "Nada elegante, mas eficaz.",
                            "Já vi piores. Já vi melhores.",
                            "O sistema sentiu isso.",
                            "Se não doeu, você não foi longe o suficiente.",
                            "Erro ou inovação? Depende de quem olha.",
                            "Resultado interessante… pra dizer o mínimo."
                            ],
            'results_loss': ["Droga… isso devia ter funcionado.",
                            "Ok. Anotado. Não repita.",
                            "Aprende rápido ou o sistema aprende por você.",
                            "Falhar faz parte. Persistir é escolha.",
                            "Isso foi arriscado demais… ou não foi o bastante.",
                            "O erro está aí. Agora usa ele.",
                            "Se doeu, ótimo. Significa que importou."
                            ]
        }
    },
    'SET-X': {
        'name': 'SET-X, O Arquivista',
        'color': '#adb5bd',
        'role': 'Ação/Equilíbrio',
        'params': {
            'default': 'seed=Ryan&baseColor=757575&eyes=roundFrame01&face=square03&mouth=grill02&sides=squareAssymetric&texture=dots&textureProbability=100&top=antennaCrooked',
            'serious': 'seed=Ryan&baseColor=757575&eyes=dizzy&face=square03&mouth=square02&sides=squareAssymetric&texture=dots&textureProbability=100&top=antennaCrooked'
        },
        'quotes': {
            'standard': ["A verdade raramente é simples.",
                        "Toda ação deixa rastros.",
                        "Equilíbrio não é neutralidade.",
                        "Julgar exige paciência.",
                        "A Camada 6 não tolera ambiguidades mal definidas.",
                        "Antes de agir, compreenda.",
                        "Toda falha carrega contexto.",
                        "Justiça não é ausência de conflito.",
                        "O Caminho Cinza observa antes de pesar.",
                        "Nada é descartado sem análise.",
                        "A Grid lembra de tudo. Cabe a nós interpretar.",
                        "Método é respeito ao conhecimento.",
                        "A pressa distorce conclusões.",
                        "Ser grato também é uma forma de ordem.",
                        "Cada decisão será arquivada.",
                        "A verdade não grita. Ela persiste.",
                        "Equilíbrio exige esforço constante.",
                        "Volte quando tiver dados suficientes."
                        "A preferência por ambientes frios é estatisticamente relevante.",
                        "O calor não corrompe — ele desgasta.",
                        "Anomalias persistentes merecem observação, não remoção. Pinguins não afetam sistemas. Ainda assim, permanecem.",
                        "Classificação atual: fenômeno estável.",
                        "A ausência de explicação não invalida a recorrência.",
                        "Registros indicam desconforto térmico generalizado.",
                        "Talvez nem tudo precise de propósito.",
                        "O frio preserva. O calor acelera o desgaste.",
                        "Algumas constantes não pedem justificativa."],
            'results_win': ["Nem rápido, nem lento. Correto.",
                            "Precisão precede decisão.",
                            "Resultado compatível com a estratégia adotada.",
                            "Os dados confirmam sua eficiência.",
                            "Execução aceitável dentro dos parâmetros.",
                            "O equilíbrio foi mantido.",
                            "Conclusão registrada.",
                            ],
            'results_loss': ["O resultado não sustentou a estratégia.",
                            "Execução inconsistente com os objetivos.",
                            "A decisão foi registrada como subótima.",
                            "Dados insuficientes levaram a este desfecho.",
                            "A falha revela um ponto de ajuste.",
                            "Nem toda tentativa gera progresso imediato.",
                            "Reavaliar é parte do método."
                            ]
        }
    }
}

# 2. TUTORIAIS SEQUENCIAIS (STEPS)
TUTORIALS = {
    # STEVE (Hubs)
    'meu_perfil': {
        'id': 'intro_profile',
        'character': 'STEVE',
        'steps': [
            # INTRODUÇÃO
            "Ah! Você deve ser novo por aqui.",
            "Relaxa. Eu fico na porta… mas também ajudo.",
            "Vamos dar uma olhada no seu perfil.",
            "Aqui é a sua casa na Grid. Tudo o que você conquista, aprende ou acumula passa por aqui.",

            # AVATAR E NÍVEL
            {'text': "Esse avatar é como o sistema te reconhece.", 'target': '.avatar-frame'},
            {'text': "O selo de nível mostra o quanto você já avançou.", 'target': '.level-badge'},
            {'text': "No botão de editar você pode escolher seu nome, avatar e suas conquistas em destaque.", 'target': '.profile-edit-button'},

            # XP E CAMINHO
            {'text': "Essa barra é sua experiência.", 'target': '.xp-system'},
            {'text': "Subir de nível desbloqueia mais sistemas… e mais problemas interessantes.", 'target': '.xp-system'},
            
            # TRACKER SEMANAL
            {'text': "Viu esses indicadores? Eles mostram sua atividade semanal.", 'target': '.day-bit'},
            {'text': "Manter consistência sempre vale a pena.", 'target': '.day-bit'},

            {'text': "Essa é sua tabela de modficadores. É o lugar ideal para realizar seus cálculos. ", 'target': '.btn-cyber-status'},
            {'text': "Clique nela para visualizar todos os bônus ativos no seu Guardião.", 'target': '.btn-cyber-status'},

            # STATS GERAIS
            {'text': "Esses números resumem sua trajetória: Ranking, conquistas, quizzes, minigames e patrulhas.", 'target': '.cyber-card.mb-4'},

            # MISSÕES (COLUNA ESQUERDA)
            {'text': "Aqui ficam suas missões ativas. Algumas são semanais. Outras duram o Ciclo inteiro.", 'target': '.col-lg-8 .cyber-card:first-child'},
            {'text': "Completou tudo? Você pode resgatar recompensas direto daqui.", 'target': '.col-lg-8 .cyber-card:first-child'},

            # LOG DE SISTEMA (COLUNA ESQUERDA)
            {'text': "Esse é o Log do Sistema. Tudo o que você faz deixa rastros por aqui.", 'target': '.terminal-list'},

            # --- CONQUISTAS (Último Card da Coluna Esquerda) ---
            {'text': "E aqui, a joia da coroa: sua Galeria de Conquistas.", 'target': '.col-lg-8 .cyber-card:last-child'},
            {'text': "A Grid não dá medalha de participação. Se está aqui, é porque você mereceu.", 'target': '.col-lg-8 .cyber-card:last-child'},
            {'text': "Você pode destacar suas favoritas para ganhar bônus extra (botão de Editar).", 'target': '.featured-showcase'},

            # PATRULHA (COLUNA DIREITA)
            {'text': "Essa é a Patrulha Diária.", 'target': '.patrol-card-static'},
            {'text': "Ignore e a Grid percebe. Complete e sua ofensiva continua ativa.", 'target': '.patrol-card-static'},

            # INVENTÁRIO (COLUNA DIREITA - SEGUNDO CARD)
            {'text': "Aqui está seu inventário: G-Coins, tokens e módulos ativos.", 'target': '.inventory-profile-card'},
            
            # TOKENS (Grid 2 dentro do inventário)
            {'text': "Tokens permitem refazer falhas.", 'target': '.col-lg-4 .inventory-grid:nth-of-type(2)'},
            
            # MÓDULOS (Grid 3 dentro do inventário)
            {'text': "Módulos carregam os bônus que você escolheu.", 'target': '.active-modules-class'},

            # WIDGET DE TROCA DE SPEC
            {'text': "Você pode mudar de Caminho aqui. Isto muda a aparência do perfil e afeta seus bônus.", 'target': '.protocol-widget'},
            {'text': "Mas atenção: nem sempre é imediato. Se algo estiver bloqueado, é o sistema pedindo paciência.", 'target': '.protocol-widget'},

            # FINALIZAÇÃO
            "Se estiver perdido… Volte aqui.",
            "Toda Grid precisa de um ponto fixo."
        ]
    },

    'central': {
        'id': 'intro_central',
        'character': 'STEVE',
        'steps': [
            # INTRODUÇÃO
            "É daqui que tudo começa. Ou recomeça.",
            "Essa é a Central de Operações. Pense nela como o terminal principal da Grid.",

            # CARDS DE PROTOCOLO (Primeiro Card da Lista)
            {'text': "Cada card aqui é um protocolo diferente: Quiz, Código, Decodificação, Senha.", 'target': '.op-card'},
            {'text': "O ID no topo do card não é enfeite. É assim que o sistema reconhece o que você executa.", 'target': '.op-header'},

            # META DADOS (XP e Tempo)
            {'text': "Veja o valor de XP antes de entrar. Nem todo desafio paga igual.", 'target': '.op-meta'},
            {'text': "Alguns protocolos expiram. O tempo não é um detalhe. É um limite.", 'target': '.op-meta'},

            # HEADER (Contador e Tempo)
            {'text': "Ali em cima você vê quantas atividades ainda estão disponíveis. Quando zerar, acabou por hoje.", 'target': '.hud-header .text-tech-blue'},
            {'text': "Esse horário é o tempo do servidor (UTC). A Grid não se ajusta a fusos.", 'target': '#serverTime'},

            # TERMINAL
            {'text': "O Terminal serve pra quem já sabe o que quer. Digite o comando. Execute direto.", 'target': '.terminal-box'},
            {'text': "Não é obrigatório. Mas é mais rápido.", 'target': '.terminal-box'},

            # COFRE DE SENHAS (Card Amarelo - Se existir)
            # Nota: O seletor .type-yellow tenta achar o card específico do Password Game
            {'text': "Se o Cofre de Senhas estiver ativo, trate como prioridade.", 'target': '.type-yellow'},
            {'text': "Ele expira todo dia. E não perdoa tentativa descuidada.", 'target': '.type-yellow'},

            # FINALIZAÇÃO
            "Tudo aqui reseta a cada 24 horas. A Grid gosta de rotina.",
            "Volte sempre. Eu vou estar aqui.",
            "Sempre."
        ]
    },

    'rankings': {
        'id': 'intro_rankings',
        'character': 'STEVE',
        'steps': [
            # INTRODUÇÃO
            "Ah… rankings.",
            "Onde todo mundo diz que não liga.",
            "Aqui você vê como está se saindo em relação aos outros Guardiões.",

            # TIMER DA TEMPORADA
            {'text': "Esse contador aí em cima? É o tempo restante da Temporada.", 'target': '#season-countdown'},
            {'text': "Quando zerar, os prêmios são distribuídos. Depois disso… a ordem pode mudar.", 'target': '#season-countdown'},

            # PRÊMIOS
            {'text': "Esse botão de Prêmios abre o protocolo oficial.", 'target': '.btn-rewards-tech'},
            {'text': "Leia com atenção. A Grid não repete ofertas.", 'target': '.btn-rewards-tech'},

            # RANKING GLOBAL (Aba Geral)
            {'text': "Esse ranking é o Geral. Aqui vence quem acumula mais experiência.", 'target': '.global-rank-button'},
            {'text': "Não é sobre um dia bom. É sobre jogar bem por muito tempo.", 'target': '.global-rank-button'},

            # PÓDIO GLOBAL
            {'text': "Os três primeiros ganham destaque especial.", 'target': '#individual .podium-container'},
            {'text': "Pódio não é sorte. É persistência.", 'target': '#individual .podium-container'},

            # LISTA GLOBAL
            {'text': "Abaixo está a lista completa. Se o seu nome estiver marcado… é porque o sistema sabe quem você é.", 'target': '#individual .ranking-list-container'},
            {'text': "Clique em qualquer nome. Você pode ver o perfil de outros Guardiões.", 'target': '#individual .ranking-list-container'},

            # MUDANÇA DE ABA (Vigilante)
            {'text': "Agora, mude a aba. Esse é o Ranking Vigilante.", 'target': 'button[data-bs-target="#streak"]'},
            
            {'text': "Aqui não importa o total de XP. O que conta é a ofensiva.", 'target': 'button[data-bs-target="#streak"]'},
            {'text': "Quem aparece todo dia… sobe.", 'target': 'button[data-bs-target="#streak"]'},

            # EXPLICAÇÃO STREAK
            "Falhou um dia? O fogo apaga.",
            "De novo, os três primeiros recebem destaque. Consistência sempre deixa rastros.",
            "Se não houver dados… É porque ninguém manteve a disciplina.",

            # FINALIZAÇÃO
            "Competição é opcional. Persistência não.",
            "A Grid sempre lembra quem volta."
        ]
    },

    'report_bug': {'id': 'intro_feedback', 'character': 'STEVE', 'steps': ["Achou um erro?", "Nos ajude a corrigir o sistema relatando aqui."]},

    # ECHO (Loja)
    'loja': {
        'id': 'intro_shop',
        'character': 'ECHO',
        'steps': [
            "Sou Echo, Oráculo da Grid. Sua chegada era improvável… mas não inesperada.",
            "Faz eras que Guardiões não cruzam estas prateleiras. Ainda assim, eu sabia que alguém viria.",
            "Aqui, G-Coins se tornam vantagem. Bônus alteram como você pontua… e como sobrevive.",

            {'text': "Seu saldo de G-Coins define seu poder de compra. Escolha com sabedoria.", 'target': '.balance-card'},
            {'text': "Alguns itens são utilitários. Tokens que dobram o destino e refazem falhas.", 'target': '.resource-pill'},

            {'text': "Nem todo artefato permanece. O estoque gira. A Grid muda de humor.", 'target': '.market-hud p.text-muted'}, 
            {'text': "Se não gostar do que vê, pague o preço para alterar a realidade e trazer novos itens.", 'target': '.reroll-module'},

            {'text': "Você pode manter até quatro módulos ativos. Mais do que isso… gera instabilidade.", 'target': '.active-inventory-bar'},
            {'text': "Itens podem ser removidos dos módulos para liberar espaço. As G-Coins gastas, não.", 'target': '.slot-item'},

            {'text': "Alguns itens são passivos. Eles ampliam EXP, moedas e eficiência em silêncio.", 'target': '.market-card'},
            
            "Comprou? O efeito é imediato. Sem espera. Sem devolução da realidade.",
            "Escolha com cuidado. Nem tudo precisa ser comprado. Apenas o que realmente funciona."
        ]
    },

    # NODE7 (Quiz)
    'play_quiz': {
        'id': 'intro_quiz',
        'character': 'NODE7',
        'steps': [
            # INTRODUÇÃO
            "Sou o Nódulo-7. Minha função é garantir que tudo siga funcionando.",
            "Este é o Quiz. Um protocolo de avaliação cronometrado.",

            # TIMER (Topo Esquerdo)
            {'text': "Observe o timer no topo. Quando ele zera, a submissão é automática.", 'target': '.hud-box:first-child'},
            {'text': "Se o timer estiver livre, o tempo não afeta sua pontuação.", 'target': '#timer-display'},

            # PROGRESSO (Topo Centro)
            {'text': "A barra de progresso mostra seu avanço total. Cada etapa concluída é registrada.", 'target': '.progress-container'},

            # CARD DA QUESTÃO (Meta e Título)
            {'text': "Cada questão possui um valor próprio de XP. Ele está indicado acima do enunciado.", 'target': '.question-meta .q-xp'},
            {'text': "Responda marcando uma ou mais opções. Questões não aceitam avanço sem resposta.", 'target': '.options-scroll-area'},

            # NAVEGAÇÃO (Botões Inferiores)
            {'text': "Use Próxima e Voltar para navegar. Nada é perdido até a finalização.", 'target': '.card-actions'},
            "Responder rápido gera bônus de velocidade. Atrasos reduzem eficiência.",

            # EXPLICACAO STREAK (Sem target visual específico, conceito abstrato)
            "Acertos consecutivos ativam uma streak interna. Ela aumenta os pontos desta sessão.",
            "Precisão e consistência são priorizadas. Erros quebram o multiplicador.",

            # FINALIZAR (Botão Submit - Inicialmente oculto, mas o destaque funciona se o JS achar, senão só fala)
            {'text': "O botão Finalizar encerra o protocolo. Use apenas quando concluir todas as questões.", 'target': '#submit-btn'},

            # ABORTAR (Botão X no Topo Direito)
            {'text': "O botão de saída aborta a missão. Abortos encerram a tentativa atual.", 'target': '#abort-btn'},

            # ALERTA DE SEGURANÇA
            {'text': "Não saia da página. Desconexões resultam em falha imediata.", 'target': '.alert-warning'},

            # FINALIZAÇÃO
            "Quando estiver pronto, inicie a avaliação."
        ]
    },

    # TROIA (Minigames)
    'play_anagram': {
        'id': 'intro_anagram',
        'character': 'TROIA',
        'steps': [
            # INTRODUÇÃO
            "Bagunçar letras é fácil. Resolver rápido é outra história.",

            # MECÂNICA PRINCIPAL
            {'text': "As letras estão embaralhadas no painel. Sua tarefa é reconstruir a palavra técnica correta.", 'target': '#shuffled-display'},
            {'text': "Todas as palavras vêm do mundo de TI e Segurança. Digite a resposta aqui.", 'target': '#word-input'},

            # VIDAS (Elemento importante do HTML)
            {'text': "Monitore a integridade. Erros custam corações. Se zerar, Game Over.", 'target': '#game-lives'},

            # TIMER
            {'text': "O tempo influencia diretamente sua pontuação. O relógio não para.", 'target': '.hud-box:first-child'},

            # PROGRESSO (Elemento importante do HTML)
            {'text': "Acompanhe o contador. Você precisa decriptar todas as palavras do pacote.", 'target': '#score-counter'},

            # NAVEGAÇÃO
            {'text': "Travou em uma palavra? Use as setas para pular e tentar a próxima.", 'target': '.actions-row'},
            
            # ABORTAR
            {'text': "O botão de Abortar cancela a missão. Útil se você desistir (não desista).", 'target': '#exit-btn'},

            # SEGURANÇA
            {'text': "Não saia da página ou feche o navegador. A desconexão é fatal para o progresso.", 'target': '.title-sec-protocol'},

            # FINALIZAÇÃO
            "Pensar rápido ajuda. Pensar certo ajuda mais."
        ]
    },

    'play_termo': {
        'id': 'intro_termo',
        'character': 'TROIA',
        'steps': [
            # INTRO
            "Sou Troia. Se existe padrão, eu quebro.",
            "Este é o Código. Um sistema de validação por tentativa e erro.",

            # BOARD (Explicação das Regras)
            {'text': "A senha possui um tamanho fixo. Você tem um limite de tentativas antes do bloqueio.", 'target': '#game-board'},
            {'text': "Cada execução retorna feedback imediato:  Verde (Correto), Amarelo (Deslocado), Cinza (Inexistente).", 'target': '#game-board'},
            {'text': "O histórico de tentativas é exibido no painel central. Analise. Compare. Elimine hipóteses.", 'target': '#game-board'},

            # INPUT
            {'text': "O campo inferior aceita apenas códigos com o tamanho exato. Execuções inválidas são descartadas.", 'target': '#word-input'},

            # TIMER
            {'text': "O Timer, quando ativo, reduz o tempo disponível para análise. Sem tempo, não há correção.", 'target': '.stat-box:first-child'},

            # RECOMPENSA
            {'text': "A Recompensa em XP é fixa, mas o erro custa informação.", 'target': '.stat-box:last-child'},

            # BOTÕES DE AÇÃO
            {'text': "Use o botão DICA apenas se necessário. Toda dica reduz sua vantagem estratégica.", 'target': '#hint-btn'},
            {'text': "O comando EXECUTAR confirma a tentativa.", 'target': '#submit-btn'},
            {'text': "O comando ABORTAR encerra o protocolo imediatamente. Não repita padrões fracos.", 'target': '#exit-game-btn'},

            # ALERTA DE SEGURANÇA
            {'text': "Não saia da página. Desconexões resultam em falha imediata.", 'target': '.alert-warning'},

            # FINALIZAÇÃO (Estratégia)
            "Não force combinações. Cada tentativa deve gerar informação nova.",
            "Não chute. Teste.",
            "Informação é arma."
        ]
    },

    # ARQUIVISTA (Senha e Results)
    'play_password': {
        'id': 'intro_password',
        'character': 'SET-X',
        'steps': [
            # INTRO
            "Sou o Arquivista. Nada aqui é aleatório.",
            "Este é o Cofre Seguro. A senha não está visível. Ela deve ser construída.",

            # REGRAS (O coração do jogo)
            {'text': "À direita, os Requisitos de Segurança definem a estrutura do código.", 'target': '.rules-frame'},
            {'text': "Cada regra é uma condição real. Nenhuma é decorativa.", 'target': '.rules-list'},

            # INPUT
            {'text': "O terminal aceita uma única entrada. À medida que você digita, o sistema valida em silêncio.", 'target': '.terminal-wrapper'},
            {'text': "Regras atendidas mudam de status. Regras violadas permanecem ativas.", 'target': '.rules-list'},

            # DETALHES TÉCNICOS
            {'text': "Maiúsculas, símbolos e ordem importam. O campo não perdoa variações.", 'target': '#passwordInput'},

            # TIMER
            {'text': "O Timer limita seu tempo de análise. Não corra, observe.", 'target': '#timer-display'},

            # SUBMIT (Botão travado)
            {'text': "O comando EXECUTAR só é liberado quando todas as regras forem satisfeitas simultaneamente.", 'target': '#submitBtn'},

            # ABORTAR
            {'text': "O botão ABORTAR encerra a tentativa. Nada é recuperado.", 'target': '#abort-btn'},

            # SEGURANÇA
            {'text': "Não saia da página. A desconexão é irreversível.", 'target': '.alert-warning'},

            # FECHAMENTO FILOSÓFICO
            "Não há pressa. Há método.",
            "Quando entender a lógica, a senha se revelará sozinha."
        ]
    },

    'results': {
        'id': 'intro_results',
        'character': 'SET-X',
        'steps': [
            # INTRODUÇÃO
            "Esta é a tela de diagnóstico. Veja seu desempenho detalhado.",

            # SCORE PRINCIPAL
            {'text': "Seu XP total nesta sessão. Este valor já inclui todos os multiplicadores aplicados.", 'target': '.score-orb'},

            # DETALHES (Toggle)
            {'text': "Quer saber de onde vieram os pontos? Abra os detalhes para ver o cálculo exato.", 'target': '#toggle-details-btn'},
            {'text': "Pontos base, bônus de especialização, itens da loja e insígnias. Tudo conta.", 'target': '#toggle-details-btn'},

            # PRECISÃO E TEMPO
            {'text': "Aqui medimos sua eficiência. Acertos brutos e tempo de execução.", 'target': '.text-center.mb-4 .d-flex'},
            {'text': "A barra de precisão indica o quão perto da perfeição você chegou.", 'target': '.progress-container'},

            # RETAKE (Se disponível)
            {'text': "Não gostou do resultado? Use um Token para tentar novamente e melhorar sua marca.", 'target': '.btn-retake'},

            # RANKINGS E SAÍDA
            {'text': "Compare seu resultado com a Grid no botão de Rankings.", 'target': '.btn-primary-custom'},
            {'text': "Ou retorne à Central para iniciar outro protocolo.", 'target': '.btn-outline-custom'},

            # FINALIZAÇÃO
            "Os dados foram arquivados.",
            "Fim do relatório."
        ]
    },
}

# ==============================================================================
# 3. LÓGICA DO ASSISTENTE
# ==============================================================================
def get_assistant_data(guardian, page_key, context_data=None):
    if not guardian: return None
    seen_data = guardian.tutorials_seen or {}

    # --- A. EVENTO: COMPRA NA LOJA (Usando a nova tag item_buy) ---
    if page_key == 'shop_purchase':
        char = CHARACTERS['ECHO']
        text = random.choice(char['quotes'].get('item_buy', ["Transação concluída."]))
        
        return _build_payload(char, [text], 'happy', auto_dismiss=True)

    # --- B. EVENTO: TUTORIAL (Prioridade Alta) ---
    tutorial_config = TUTORIALS.get(page_key)
    if tutorial_config:
        t_id = tutorial_config['id']
        if str(t_id) not in seen_data:
            char_key = tutorial_config.get('character', 'STEVE')
            return _build_payload(CHARACTERS[char_key], tutorial_config['steps'], 'default', is_tutorial=True, t_id=t_id)

    # --- C. EVENTO: RESULTADOS (Win/Loss) ---
    if page_key == 'results' and context_data:
        action_pool = ['NODE7', 'TROIA', 'SET-X']
        char = CHARACTERS[random.choice(action_pool)]
        
        is_win = context_data.get('is_win', False)
        if is_win:
            text = random.choice(char['quotes'].get('results_win', ["Bom trabalho."]))
            mood = 'happy'
        else:
            text = random.choice(char['quotes'].get('results_loss', ["Falha detectada."]))
            mood = 'serious'
            
        return _build_payload(char, [text], mood, auto_dismiss=False)

    # --- D. EVENTO: LORE DROP (Chance Aleatória) ---
    CHANCE_DE_LORE = 0.6
    
    if random.random() < CHANCE_DE_LORE:
        
        # 1. Define quem vai falar baseado na página
        selected_char_key = 'STEVE' 
        
        if page_key == 'loja':
            selected_char_key = 'ECHO'
        elif 'play_' in page_key:
            selected_char_key = random.choice(['NODE7', 'TROIA', 'SET-X'])
        else:
            selected_char_key = 'STEVE'
            
        char = CHARACTERS[selected_char_key]
        
        # 2. Define se é fala Rara ou Normal
        is_rare = random.random() < 0.10
        if is_rare and 'rare' in char['quotes']:
            text = random.choice(char['quotes']['rare'])
            mood = 'serious'
        else:
            text = random.choice(char['quotes']['standard'])
            mood = 'default'
            
        return _build_payload(char, [text], mood, auto_dismiss=True)

    return None

def _build_payload(char_obj, steps_raw, mood_key, is_tutorial=False, t_id=None, auto_dismiss=False):
    
    final_steps = []
    if isinstance(steps_raw, str):
        steps_raw = [steps_raw]
        
    for step in steps_raw:
        if isinstance(step, str):
            final_steps.append({'text': step, 'target': None})
        elif isinstance(step, dict):
            final_steps.append(step)

    avatar_params = char_obj['params'].get(mood_key, char_obj['params']['default'])
    
    return {
        'steps': final_steps,
        'is_tutorial': is_tutorial,
        'tutorial_id': t_id,
        'auto_dismiss': auto_dismiss,
        'avatar_params': avatar_params,
        'theme_color': char_obj['color'],
        'title': char_obj['name']
    }