import random

import util
from capture import GameState
from captureAgents import CaptureAgent
from game import Action
from game import Directions

import random
import time
import util

from captureAgents import CaptureAgent
from game import Directions
from util import nearestPoint

def createTeam(firstIndex, secondIndex, isRed,
               first='AgenteTimido', second='AgenteDefensivo'):
    return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class AgenteCapturaReflexo(CaptureAgent):
    # Inicializa o estado do agente
    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        actions = gameState.getLegalActions(self.index)
        values = [self.evaluate(gameState, a) for a in actions]

        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            # If there's almost no food left, return to the start position
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        # esse retorno é para retornar a ação que tem o maior valor
        return random.choice(bestActions)
    def chooseAction(self, gameState: GameState) -> Action:
        """
        Picks among actions randomly.
        """
        actions = gameState.getLegalActions(self.index)

        '''
        You should change this in your own agent.
        '''

        return random.choice(actions)

