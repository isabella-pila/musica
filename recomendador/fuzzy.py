import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Variáveis
valence      = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'valence')
energy       = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'energy')
acousticness = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'acousticness')
popularity   = ctrl.Antecedent(np.arange(0, 101, 1),     'popularity')
nostalgia    = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'nostalgia')

playlist_score = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'playlist_score')

# Memberships — entradas
valence['triste'] = fuzz.trimf(valence.universe, [0, 0, 0.45])
valence['neutra'] = fuzz.trimf(valence.universe, [0.35, 0.5, 0.65])
valence['feliz']  = fuzz.trimf(valence.universe, [0.55, 1, 1])

energy['calma']    = fuzz.trimf(energy.universe, [0, 0, 0.45])
energy['moderada'] = fuzz.trimf(energy.universe, [0.35, 0.5, 0.65])
energy['agitada']  = fuzz.trimf(energy.universe, [0.55, 1, 1])

acousticness['eletronica'] = fuzz.trimf(acousticness.universe, [0, 0, 0.45])
acousticness['mista']      = fuzz.trimf(acousticness.universe, [0.35, 0.5, 0.65])
acousticness['acustica']   = fuzz.trimf(acousticness.universe, [0.55, 1, 1])

popularity['underground'] = fuzz.trimf(popularity.universe, [0, 0, 40])
popularity['conhecida']   = fuzz.trimf(popularity.universe, [30, 50, 70])
popularity['mainstream']  = fuzz.trimf(popularity.universe, [60, 100, 100])

nostalgia['lancamentos'] = fuzz.trimf(nostalgia.universe, [0, 0, 0.45])
nostalgia['recente']     = fuzz.trimf(nostalgia.universe, [0.35, 0.5, 0.65])
nostalgia['classico']    = fuzz.trimf(nostalgia.universe, [0.55, 1, 1])

# Memberships — saída com 5 níveis
playlist_score['muito_baixa'] = fuzz.trimf(playlist_score.universe, [0,    0,    0.25])
playlist_score['baixa']       = fuzz.trimf(playlist_score.universe, [0.15, 0.3,  0.45])
playlist_score['media']       = fuzz.trimf(playlist_score.universe, [0.35, 0.5,  0.65])
playlist_score['alta']        = fuzz.trimf(playlist_score.universe, [0.55, 0.7,  0.85])
playlist_score['muito_alta']  = fuzz.trimf(playlist_score.universe, [0.75, 1,    1   ])

rules = [

    # -------------------------------------------------------
    # CATEGORIA 1: EMOÇÃO + ENERGIA (base emocional)
    # -------------------------------------------------------
    # Feliz + agitado = eufórico
    ctrl.Rule(valence['feliz'] & energy['agitada'],   playlist_score['muito_alta']),
    # Feliz + moderado = animado
    ctrl.Rule(valence['feliz'] & energy['moderada'],  playlist_score['alta']),
    # Feliz + calmo = leve/positivo
    ctrl.Rule(valence['feliz'] & energy['calma'],     playlist_score['media']),
    # Neutro + agitado = intenso sem emoção clara
    ctrl.Rule(valence['neutra'] & energy['agitada'],  playlist_score['alta']),
    # Neutro + moderado = equilibrado
    ctrl.Rule(valence['neutra'] & energy['moderada'], playlist_score['media']),
    # Neutro + calmo = introspectivo leve
    ctrl.Rule(valence['neutra'] & energy['calma'],    playlist_score['baixa']),
    # Triste + moderado = melancólico funcional
    ctrl.Rule(valence['triste'] & energy['moderada'], playlist_score['baixa']),
    # Triste + calmo = depressivo
    ctrl.Rule(valence['triste'] & energy['calma'],    playlist_score['muito_baixa']),
    # Triste + agitado = angustiado/tenso
    ctrl.Rule(valence['triste'] & energy['agitada'],  playlist_score['baixa']),

    # -------------------------------------------------------
    # CATEGORIA 2: ACÚSTICA + ENERGIA
    # -------------------------------------------------------
    # Eletrônico agitado = dance/club
    ctrl.Rule(acousticness['eletronica'] & energy['agitada'],  playlist_score['muito_alta']),
    # Eletrônico moderado = house/pop eletrônico
    ctrl.Rule(acousticness['eletronica'] & energy['moderada'], playlist_score['alta']),
    # Eletrônico calmo = ambient/lo-fi
    ctrl.Rule(acousticness['eletronica'] & energy['calma'],    playlist_score['media']),
    # Misto moderado = indie/alternativo
    ctrl.Rule(acousticness['mista'] & energy['moderada'],      playlist_score['media']),
    # Misto agitado = rock alternativo
    ctrl.Rule(acousticness['mista'] & energy['agitada'],       playlist_score['alta']),
    # Misto calmo = folk elétrico suave
    ctrl.Rule(acousticness['mista'] & energy['calma'],         playlist_score['baixa']),
    # Acústico calmo = intimista/contemplativo
    ctrl.Rule(acousticness['acustica'] & energy['calma'],      playlist_score['baixa']),
    # Acústico moderado = singer-songwriter
    ctrl.Rule(acousticness['acustica'] & energy['moderada'],   playlist_score['media']),
    # Acústico agitado = folk animado
    ctrl.Rule(acousticness['acustica'] & energy['agitada'],    playlist_score['alta']),

    # -------------------------------------------------------
    # CATEGORIA 3: POPULARIDADE
    # -------------------------------------------------------
    # Mainstream + feliz = hit pop
    ctrl.Rule(popularity['mainstream'] & valence['feliz'],             playlist_score['muito_alta']),
    # Mainstream + neutro + agitado = hit de rádio agitado
    ctrl.Rule(popularity['mainstream'] & valence['neutra'] & energy['agitada'], playlist_score['alta']),
    # Mainstream + neutro + moderado = trilha de fundo social
    ctrl.Rule(popularity['mainstream'] & valence['neutra'] & energy['moderada'], playlist_score['media']),
    # Mainstream + triste = hit melancólico famoso
    ctrl.Rule(popularity['mainstream'] & valence['triste'],            playlist_score['baixa']),
    # Conhecida + feliz = agradável para todos
    ctrl.Rule(popularity['conhecida'] & valence['feliz'],              playlist_score['alta']),
    # Conhecida + neutro = confortável/familiar
    ctrl.Rule(popularity['conhecida'] & valence['neutra'],             playlist_score['media']),
    # Conhecida + triste = balada conhecida
    ctrl.Rule(popularity['conhecida'] & valence['triste'],             playlist_score['baixa']),
    # Underground + feliz = indie alternativo feliz
    ctrl.Rule(popularity['underground'] & valence['feliz'],            playlist_score['media']),
    # Underground + neutro = experimental/nicho
    ctrl.Rule(popularity['underground'] & valence['neutra'],           playlist_score['baixa']),
    # Underground + triste = obscuro/dark
    ctrl.Rule(popularity['underground'] & valence['triste'],           playlist_score['muito_baixa']),

    # -------------------------------------------------------
    # CATEGORIA 4: NOSTALGIA
    # -------------------------------------------------------
    # Clássico + feliz + agitado = festa retrô / hino atemporal
    ctrl.Rule(nostalgia['classico'] & valence['feliz'] & energy['agitada'],   playlist_score['muito_alta']),
    # Clássico + feliz + moderado = clássico animado
    ctrl.Rule(nostalgia['classico'] & valence['feliz'] & energy['moderada'],  playlist_score['alta']),
    # Clássico + triste + acústico = balada antiga intimista
    ctrl.Rule(nostalgia['classico'] & valence['triste'] & acousticness['acustica'], playlist_score['muito_baixa']),
    # Clássico + triste + moderado = balada melancólica clássica
    ctrl.Rule(nostalgia['classico'] & valence['triste'] & energy['moderada'], playlist_score['baixa']),
    # Clássico + underground = cult/obscuro antigo
    ctrl.Rule(nostalgia['classico'] & popularity['underground'],              playlist_score['baixa']),
    # Clássico + mainstream = hino consagrado
    ctrl.Rule(nostalgia['classico'] & popularity['mainstream'],               playlist_score['muito_alta']),
    # Recente + feliz = indie pop atual
    ctrl.Rule(nostalgia['recente'] & valence['feliz'] & acousticness['acustica'], playlist_score['alta']),
    # Recente + conhecido = hit do momento
    ctrl.Rule(nostalgia['recente'] & popularity['conhecida'],                 playlist_score['media']),
    # Lançamento + agitado + mainstream = hit novo de rádio
    ctrl.Rule(nostalgia['lancamentos'] & energy['agitada'] & popularity['mainstream'], playlist_score['muito_alta']),
    # Lançamento + eletrônico + agitado = EDM novo
    ctrl.Rule(nostalgia['lancamentos'] & acousticness['eletronica'] & energy['agitada'], playlist_score['muito_alta']),
    # Lançamento + underground = descoberta nova
    ctrl.Rule(nostalgia['lancamentos'] & popularity['underground'],           playlist_score['media']),

    # -------------------------------------------------------
    # CATEGORIA 5: VIBES ESPECÍFICAS
    # -------------------------------------------------------
    # Academia / Pump Up
    ctrl.Rule(energy['agitada'] & valence['feliz'] & acousticness['eletronica'],   playlist_score['muito_alta']),
    # Bossa Nova / Chill acústico feliz
    ctrl.Rule(valence['feliz'] & energy['calma'] & acousticness['acustica'],       playlist_score['media']),
    # Lo-fi / Study
    ctrl.Rule(valence['neutra'] & energy['calma'] & acousticness['eletronica'],    playlist_score['media']),
    # Chill House
    ctrl.Rule(valence['feliz'] & energy['calma'] & acousticness['eletronica'],     playlist_score['media']),
    # Sofrência / Dark acústico
    ctrl.Rule(valence['triste'] & acousticness['acustica'] & energy['calma'],      playlist_score['muito_baixa']),
    # Darkwave / Synthpop tenso
    ctrl.Rule(valence['triste'] & energy['agitada'] & acousticness['eletronica'],  playlist_score['baixa']),
    # Folk underground triste
    ctrl.Rule(popularity['underground'] & acousticness['acustica'] & valence['triste'], playlist_score['muito_baixa']),
    # Ambient experimental
    ctrl.Rule(popularity['underground'] & valence['neutra'] & energy['calma'],     playlist_score['baixa']),
    # Techno underground agitado
    ctrl.Rule(popularity['underground'] & acousticness['eletronica'] & energy['agitada'], playlist_score['media']),

    # -------------------------------------------------------
    # CATEGORIA 6: FALLBACKS (cobertura mínima garantida)
    # -------------------------------------------------------
    ctrl.Rule(energy['agitada'] & popularity['conhecida'],   playlist_score['alta']),
    ctrl.Rule(energy['calma']   & popularity['mainstream'],  playlist_score['media']),
    ctrl.Rule(energy['moderada'] & acousticness['mista'],    playlist_score['media']),
    ctrl.Rule(valence['neutra'] & acousticness['mista'] & popularity['conhecida'], playlist_score['media']),
]

system    = ctrl.ControlSystem(rules)
simulator = ctrl.ControlSystemSimulation(system)


def compute_fuzzy(inputs):
    simulator.input['valence']      = inputs['valence']
    simulator.input['energy']       = inputs['energy']
    simulator.input['acousticness'] = inputs['acousticness']
    simulator.input['popularity']   = inputs['popularity']
    simulator.input['nostalgia']    = inputs['nostalgia']

    simulator.compute()
    return simulator.output['playlist_score']