import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Variáveis de entrada (apenas emoção/sonoridade)
valence      = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'valence')
energy       = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'energy')
acousticness = ctrl.Antecedent(np.arange(0, 1.01, 0.01), 'acousticness')

playlist_score = ctrl.Consequent(np.arange(0, 1.01, 0.01), 'playlist_score')
#socorro
# Memberships — entradas
valence['triste'] = fuzz.trimf(valence.universe, [0, 0, 0.45])
valence['neutra'] = fuzz.trimf(valence.universe, [0.35, 0.5, 0.65])
valence['feliz']  = fuzz.trimf(valence.universe, [0.55, 1, 1])

energy['calma']    = fuzz.trimf(energy.universe, [0, 0, 0.45])
energy['moderada'] = fuzz.trimf(energy.universe, [0.35, 0.5, 0.65])
energy['agitada']  = fuzz.trimf(energy.universe, [0.55, 1, 1])

acousticness['acustica']   = fuzz.trimf(acousticness.universe, [0, 0, 0.45])
acousticness['mista']      = fuzz.trimf(acousticness.universe, [0.35, 0.5, 0.65])
acousticness['eletronica'] = fuzz.trimf(acousticness.universe, [0.55, 1, 1])

# Saída com 5 níveis
playlist_score['muito_baixa'] = fuzz.trimf(playlist_score.universe, [0,    0,    0.25])
playlist_score['baixa']       = fuzz.trimf(playlist_score.universe, [0.15, 0.3,  0.45])
playlist_score['media']       = fuzz.trimf(playlist_score.universe, [0.35, 0.5,  0.65])
playlist_score['alta']        = fuzz.trimf(playlist_score.universe, [0.55, 0.7,  0.85])
playlist_score['muito_alta']  = fuzz.trimf(playlist_score.universe, [0.75, 1,    1   ])

rules = [
    # CATEGORIA 1: EMOÇÃO + ENERGIA
    ctrl.Rule(valence['feliz']  & energy['agitada'],   playlist_score['muito_alta']),
    ctrl.Rule(valence['feliz']  & energy['moderada'],  playlist_score['alta']),
    ctrl.Rule(valence['feliz']  & energy['calma'],     playlist_score['media']),
    ctrl.Rule(valence['neutra'] & energy['agitada'],   playlist_score['alta']),
    ctrl.Rule(valence['neutra'] & energy['moderada'],  playlist_score['media']),
    ctrl.Rule(valence['neutra'] & energy['calma'],     playlist_score['baixa']),
    ctrl.Rule(valence['triste'] & energy['agitada'],   playlist_score['baixa']),
    ctrl.Rule(valence['triste'] & energy['moderada'],  playlist_score['baixa']),
    ctrl.Rule(valence['triste'] & energy['calma'],     playlist_score['muito_baixa']),

    # CATEGORIA 2: ACÚSTICA + ENERGIA
    ctrl.Rule(acousticness['eletronica'] & energy['agitada'],  playlist_score['muito_alta']),
    ctrl.Rule(acousticness['eletronica'] & energy['moderada'], playlist_score['alta']),
    ctrl.Rule(acousticness['eletronica'] & energy['calma'],    playlist_score['media']),
    ctrl.Rule(acousticness['mista']      & energy['agitada'],  playlist_score['alta']),
    ctrl.Rule(acousticness['mista']      & energy['moderada'], playlist_score['media']),
    ctrl.Rule(acousticness['mista']      & energy['calma'],    playlist_score['baixa']),
    ctrl.Rule(acousticness['acustica']   & energy['agitada'],  playlist_score['alta']),
    ctrl.Rule(acousticness['acustica']   & energy['moderada'], playlist_score['media']),
    ctrl.Rule(acousticness['acustica']   & energy['calma'],    playlist_score['baixa']),

    # CATEGORIA 3: EMOÇÃO + ACÚSTICA
    ctrl.Rule(valence['feliz']  & acousticness['eletronica'], playlist_score['muito_alta']),
    ctrl.Rule(valence['feliz']  & acousticness['acustica'],   playlist_score['alta']),
    ctrl.Rule(valence['neutra'] & acousticness['mista'],      playlist_score['media']),
    ctrl.Rule(valence['triste'] & acousticness['acustica'],   playlist_score['muito_baixa']),
    ctrl.Rule(valence['triste'] & acousticness['eletronica'], playlist_score['baixa']),

    # CATEGORIA 4: VIBES ESPECÍFICAS
   
    ctrl.Rule(valence['feliz']  & energy['agitada']  & acousticness['eletronica'], playlist_score['muito_alta']),
    
    ctrl.Rule(valence['triste'] & energy['agitada']  & acousticness['eletronica'], playlist_score['baixa']),
    # Sofrência
    ctrl.Rule(valence['triste'] & energy['calma']    & acousticness['acustica'],   playlist_score['muito_baixa']),
    # Bossa Noa / Chill
    ctrl.Rule(valence['feliz']  & energy['calma']    & acousticness['acustica'],   playlist_score['media']),
    # Lo-fi / Study
    ctrl.Rule(valence['neutra'] & energy['calma']    & acousticness['eletronica'], playlist_score['media']),
    # Folk animado
    ctrl.Rule(valence['feliz']  & energy['moderada'] & acousticness['acustica'],   playlist_score['alta']),
    # Indie alternativo
    ctrl.Rule(valence['neutra'] & energy['agitada']  & acousticness['mista'],      playlist_score['alta']),

    # CATEGORIA 5: FALLBACKS
    ctrl.Rule(energy['agitada'],   playlist_score['alta']),
    ctrl.Rule(energy['calma'],     playlist_score['baixa']),
    ctrl.Rule(valence['feliz'],    playlist_score['alta']),
    ctrl.Rule(valence['triste'],   playlist_score['muito_baixa']),
]

system    = ctrl.ControlSystem(rules)
simulator = ctrl.ControlSystemSimulation(system)


def compute_fuzzy(inputs):
    simulator.input['valence']      = inputs['valence']
    simulator.input['energy']       = inputs['energy']
    simulator.input['acousticness'] = inputs['acousticness']
    simulator.compute()
    return simulator.output['playlist_score']