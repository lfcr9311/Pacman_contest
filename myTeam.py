# myTeam.py

from captureAgents import CaptureAgent
import random, util
from game import Directions

#################
# Team creation #
#################

def createTeam(firstIndex: int, secondIndex: int, isRed: bool,
               first='DefensiveAgent', second='DefensiveAgent') -> list[CaptureAgent]:
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers. isRed is True if the red team is being created, and
  will be False if the blue team is being created.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########################
# Defensive Agent Class  #
##########################

class DefensiveAgent(CaptureAgent):
  """
  A defensive agent that protects its territory and eliminates enemies.
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)

    # Remove STOP action from legal actions if it's present
    if Directions.STOP in actions:
      actions.remove(Directions.STOP)

    if not actions:
      return Directions.STOP

    # Evaluate actions based on their impact on protecting territory and eliminating enemies
    action = self.getBestAction(gameState, actions)
    return action

  def getBestAction(self, gameState, actions):
    bestAction = None
    bestScore = float('-inf')

    for action in actions:
      successor = self.getSuccessor(gameState, action)
      score = self.evaluate(successor)

      if score > bestScore:
        bestAction = action
        bestScore = score

    return bestAction

  def evaluate(self, gameState):
    features = self.getFeatures(gameState)
    weights = self.getWeights(gameState)

    return features * weights

  def getFeatures(self, gameState):
    features = util.Counter()
    myPos = gameState.getAgentState(self.index).getPosition()
    opponents = self.getOpponents(gameState)

    # Feature: distance to nearest visible opponent (elimination)
    if len(opponents) > 0:
      visibleOpponents = [opp for opp in opponents if gameState.getAgentPosition(opp) is not None]
      if len(visibleOpponents) > 0:
        minDistanceToOpponent = min([self.getMazeDistance(myPos, gameState.getAgentPosition(opp)) for opp in visibleOpponents])
        features['distanceToOpponent'] = -minDistanceToOpponent  # Negate to maximize distance to opponent

    # Feature: distance to start (territory protection)
    features['distanceToStart'] = self.getMazeDistance(myPos, self.start)

    return features

  def getWeights(self, gameState):
    return {'distanceToOpponent': 1, 'distanceToStart': 1}

  def getSuccessor(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != util.nearestPoint(pos):
      return successor.generateSuccessor(self.index, action)
    else:
      return successor
