import random
import util

from captureAgents import CaptureAgent
from game import Directions
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='AgenteTimido', second='AgenteDefensivo'):
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

#baseado no baseline.py

class ReflexCaptureAgent(CaptureAgent):
    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)

        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):

        actions = gameState.getLegalActions(self.index)

        values = [self.evaluate(gameState, a) for a in actions]

        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):

        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()

        if pos != nearestPoint(pos):
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):

        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):

        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self, gameState, action):
        return {'successorScore': 1.0}

    def getMostDenseArea(self, gameState):
        ourFood = self.getFoodYouAreDefending(gameState).asList()
        distance = [self.getMazeDistance(gameState.getAgentPosition(self.index), a) for a in ourFood]
        nearestFood = ourFood[0]
        nearestDstance = distance[0]

        for i in range(len(distance)):
            if distance[i] < nearestDstance:
                nearestFood = ourFood[i]
                nearestDstance = distance[i]
        return nearestFood







class AgenteDefensivo(ReflexCaptureAgent):
    lastSuccess = 0
    flag = 1
    flag2 = 0
    currentFoods = []
    s = []

    def getFeatures(self, gameState, action):
        self.start = self.getMostDenseArea(gameState)

        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()
        self.s = (18, 7)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        features['Boundries'] = self.getMazeDistance(myPos, self.s)

        if (self.flag2 == 0):
            self.flag2 = 1
            self.currentFoods = self.getFoodYouAreDefending(gameState).asList()
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]

        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            pos = [a.getPosition() for a in invaders]
            nearestPos = pos[0]
            nearestDst = dists[0]

            for i in range(len(dists)):
                if dists[i] < nearestDst:
                    nearestPos = pos[i]
                    nearestDst = dists[i]

            features['invaderPDistance'] = nearestDst
            if (features['invaderDistance'] == 1 or features['invaderPDistance'] == 1 or features[
                'invaderLDistance'] == 1):
                self.flag = 0
                self.lastSuccess = nearestPos
                features['invaderLDistance'] = self.getMazeDistance(myPos, self.lastSuccess)
                self.currentFoods = self.getFoodYouAreDefending(gameState).asList()

            if (len(self.currentFoods) > len(self.getFoodYouAreDefending(gameState).asList())):
                nextFoods = self.getFoodYouAreDefending(gameState).asList()
                for i in range(len(self.currentFoods)):
                    if (len(self.currentFoods) > 0 and len(nextFoods) > i):
                        if (self.currentFoods[i][0] != nextFoods[i][0] or self.currentFoods[i][1] != nextFoods[i][1]):
                            features['invaderPDistance'] = self.getMazeDistance(myPos, self.currentFoods[i])
                            self.lastSuccess = self.currentFoods[i]
                            self.currentFoods = nextFoods
                            break

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'invaderPDistance': -20,
                'invaderLDistance': -5, 'Boundries': -10, 'stop': -100, 'reverse': -2}








class AgenteTimido(CaptureAgent):

    def __init__(self, index, timeForComputing=.1):
        CaptureAgent.__init__(self, index, timeForComputing=.1)
        self.escapepath = []
        self.eaten = 0
        self.height = 0
        self.width = 0
        self.plan = [[], []]

    def registerInitialState(self, gameState):
        self.eaten = 0
        self.height = len(gameState.getWalls()[0])
        for w in gameState.getWalls().asList():
            if w[1] == 0:
                self.width += 1
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        myPos = gameState.getAgentPosition(self.index)

        if self.getPreviousObservation() is not None:
            if self.getPreviousObservation().hasFood(myPos[0], myPos[1]):
                self.eaten += 1

        nearestFood = self.nearestFood(gameState)
        nearestEnemy = self.getNearestEnemy(gameState)

        if not gameState.getAgentState(self.index).isPacman:
            self.eaten = 0
            while len(self.plan[0]) == 0:
                y = random.choice(range(0, self.height, 1))
                if not gameState.hasWall(int(self.width / 2), y):
                    self.plan = [[int(self.width / 2) + 1, y],
                                 self.escapePath(gameState, self.width, self.height, nearestEnemy,
                                                 [int(self.width / 2), y])]
            if len(self.plan[1]) == 0:
                if not len(self.plan[0]) == 0:
                    self.plan[1] = self.escapePath(gameState, self.width, self.height, nearestEnemy, self.plan[0])
            self.escapepath = self.plan[1]
        else:
            self.plan = [[], []]
            if len(nearestEnemy) > 0:
                if nearestEnemy[1] < 4:
                    self.escapepath = self.escapePath(gameState, self.width, self.height, nearestEnemy,
                                                      [self.width / 2 - 4])
            else:
                self.escapepath = []
                if self.eaten == 5:
                    self.escapepath = self.escapePath(gameState, 36, 17, nearestEnemy, [self.width / 2 - 1])

        actions = gameState.getLegalActions(self.index)
        values = [self.evaluate(gameState, nearestFood, nearestEnemy, self.escapepath, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        action = random.choice(bestActions)
        return action

    def escapePath(self, gameState, width, height, enemy, point):
        myPos = gameState.getAgentPosition(self.index)
        path = []

        # Simplesmente move na direção oposta ao inimigo mais próximo, se houver
        if len(enemy) > 0:
            enemyPos = enemy[0]
            dx = myPos[0] - enemyPos[0]
            dy = myPos[1] - enemyPos[1]
            # Movimento para a esquerda
            if dx > 0 and not gameState.hasWall(myPos[0] - 1, myPos[1]):
                path.append((myPos[0] - 1, myPos[1]))
            # Movimento para a direita
            elif dx < 0 and not gameState.hasWall(myPos[0] + 1, myPos[1]):
                path.append((myPos[0] + 1, myPos[1]))
            # Movimento para baixo
            elif dy > 0 and not gameState.hasWall(myPos[0], myPos[1] - 1):
                path.append((myPos[0], myPos[1] - 1))
            # Movimento para cima
            elif dy < 0 and not gameState.hasWall(myPos[0], myPos[1] + 1):
                path.append((myPos[0], myPos[1] + 1))

        return path

    def nearestFood(self, gameState):
        food = self.getFood(gameState).asList()
        distance = [self.getMazeDistance(gameState.getAgentPosition(self.index), a) for a in food]

        if len(food) < 3:
            previous = self.getFoodYouAreDefending(gameState).asList()[0]
            return [previous, self.getMazeDistance(gameState.getAgentPosition(self.index), previous)]

        nearestFood = food[0]
        nearestDistance = distance[0]

        for i in range(len(distance)):
            if distance[i] < nearestDistance:
                nearestFood = food[i]
                nearestDistance = distance[i]

        return [nearestFood, nearestDistance]

    def getNearestEnemy(self, gameState):
        myPos = gameState.getAgentPosition(self.index)
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if not a.isPacman and a.getPosition() is not None]
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]

        if len(invaders) == 0:
            return []

        nearestEnemy = invaders[0].getPosition()
        nearestDistance = dists[0]

        for i in range(len(dists)):
            if dists[i] < nearestDistance:
                nearestEnemy = invaders[i].getPosition()
                nearestDistance = dists[i]

        return [nearestEnemy, nearestDistance]

    def evaluate(self, gameState, nearestFood, nearestEnemy, escapepath, action):
        score = 0

        if gameState.generateSuccessor(self.index, action).getScore() > gameState.getScore():
            score += 2

        if self.getMazeDistance(gameState.generateSuccessor(self.index, action).getAgentPosition(self.index),
                                nearestFood[0]) < nearestFood[1]:
            score += 1

        pre = self.getPreviousObservation()
        if pre is not None and pre.getAgentPosition(self.index) == gameState.generateSuccessor(self.index,
                                                                                               action).getAgentPosition(
                self.index):
            score -= 5

        if len(nearestEnemy) > 0 and nearestEnemy[1] < 4:
            if gameState.generateSuccessor(self.index, action).getAgentState(self.index).isPacman:
                score += (self.getMazeDistance(
                    gameState.generateSuccessor(self.index, action).getAgentPosition(self.index), nearestEnemy[0]) -
                          nearestEnemy[1])
                nextActions = gameState.generateSuccessor(self.index, action).getLegalActions(self.index)
                if len(nextActions) == 2:
                    score -= 100
        else:
            score += 2

        if len(escapepath) > 0:
            if [gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)[0],
                gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)[1]] in escapepath:
                if not (len(nearestEnemy) > 0 > nearestEnemy[2] and nearestEnemy[1] < 3):
                    score += 10

        if action == Directions.STOP:
            score = -10

        return score
