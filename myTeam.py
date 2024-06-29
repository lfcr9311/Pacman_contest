import random
import time
import util

from captureAgents import CaptureAgent
from game import Directions
from util import nearestPoint

def createTeam(firstIndex, secondIndex, isRed,
               first='AgenteTimido', second='AgenteReflexoDefensivo'):
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agentes #
##########

            # Inicializa o estado do agente

class AgenteCapturaReflexo(CaptureAgent):
    def registerInitialState(self, gameState):
        # Inicializa o estado do agente
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        # Choose an action based on evaluations
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

        # Choose one of the best actions
        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        # Generates the successor of the current state based on the action
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()

        if pos != nearestPoint(pos):
            # Continue generating successors until reaching a valid point
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        # Avalia a ação com base nos recursos e pesos
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
        # Obtém a área mais densa de comida que estamos defendendo
        ourFood = self.getFoodYouAreDefending(gameState).asList()
        distance = [self.getMazeDistance(gameState.getAgentPosition(self.index), a) for a in ourFood]
        nearestFood = ourFood[0]
        nearestDstance = distance[0]

        for i in range(len(distance)):
            if distance[i] < nearestDstance:
                nearestFood = ourFood[i]
                nearestDstance = distance[i]
        return nearestFood


class AgenteReflexoDefensivo(AgenteCapturaReflexo):
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
        self.caminhoDeFuga = []
        self.comidaComida = 0
        self.altura = 0
        self.largura = 0
        self.plano = [[], []]

    def registerInitialState(self, gameState):
        # Inicializa o estado do agente
        self.comidaComida = 0

        self.altura = len(gameState.getWalls()[0])
        for parede in gameState.getWalls().asList():
            if parede[1] == 0:
                self.largura += 1

        print(self.altura)
        print(self.largura)

        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        start = time.time()

        mypos = gameState.getAgentPosition(self.index)

        if self.getPreviousObservation() is not None:
            if self.getPreviousObservation().hasFood(mypos[0], mypos[1]):
                self.comidaComida += 1

        comidaMaisProxima = self.nearestFood(gameState)
        inimigoMaisProximo = self.getNearestEnemy(gameState)

        if not gameState.getAgentState(self.index).isPacman:
            self.comidaComida = 0
            while len(self.plano[0]) == 0:
                y = random.choice(range(0, self.altura, 1))
                if not gameState.hasWall(int(self.largura / 2), y):
                    self.plano = [[int(self.largura / 2) + 1, y],
                                  self.bfs(gameState, self.largura, self.altura, inimigoMaisProximo,
                                           [int(self.largura / 2), y])]
            if len(self.plano[1]) == 0:
                if not len(self.plano[0]) == 0:
                    self.plano[1] = self.bfs(gameState, self.largura, self.altura, inimigoMaisProximo, self.plano[0])
            self.caminhoDeFuga = self.plano[1]
        else:
            self.plano = [[], []]
            if len(inimigoMaisProximo) > 0:
                if inimigoMaisProximo[1] < 4:
                    self.caminhoDeFuga = self.bfs(gameState, self.largura, self.altura, inimigoMaisProximo, [self.largura / 2 - 4])
            else:
                self.caminhoDeFuga = []
                if self.comidaComida == 5:
                    self.caminhoDeFuga = self.bfs(gameState, 36, 17, inimigoMaisProximo, [2, 2])

        plan1 = []
        if len(comidaMaisProxima) > 0:
            if len(self.caminhoDeFuga) > 0:
                plan1 = self.bfs(gameState, self.largura, self.altura, comidaMaisProxima, self.caminhoDeFuga[0])
            else:
                plan1 = comidaMaisProxima

        action = None
        if len(plan1) > 0:
            action = self.getAction(gameState, plan1[0])
        else:
            if len(self.caminhoDeFuga) > 0:
                action = self.getAction(gameState, self.caminhoDeFuga[0])
            else:
                actions = gameState.getLegalActions(self.index)
                action = random.choice(actions)

        self.debugDraw(mypos, [0, 0, 0], clear=True)
        self.debugDraw(self.caminhoDeFuga, [1, 0, 0], clear=True)
        return action

    def getAction(self, gameState, state):
        actions = gameState.getLegalActions(self.index)
        for action in actions:
            successor = self.getSuccessor(gameState, action)
            if state == successor.getAgentPosition(self.index):
                return action
        return None

    def getNearestEnemy(self, gameState):
        pos = gameState.getAgentPosition(self.index)
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        pac = [a for a in enemies if a.isPacman and a.getPosition() != None]

        enemy = []
        if len(pac) > 0:
            for a in pac:
                distance = self.getMazeDistance(pos, a.getPosition())
                if len(enemy) == 0 or distance < enemy[1]:
                    enemy = [a.getPosition(), distance]
        return enemy

    def nearestFood(self, gameState):
        food = self.getFood(gameState).asList()
        pos = gameState.getAgentPosition(self.index)
        distance = []
        if len(food) > 0:
            for pellet in food:
                distance.append(self.getMazeDistance(pos, pellet))
            target = food[distance.index(min(distance))]
            return self.bfs(gameState, self.largura, self.altura, [], target)
        return []

    def bfs(self, gameState, width, height, obstacle, target):
        walls = gameState.getWalls().asList()
        closed = []
        for w in walls:
            closed.append(w)

        for ob in obstacle:
            closed.append(ob)

        state = gameState.getAgentPosition(self.index)
        open = util.PriorityQueue()
        open.push((state, []), self.getMazeDistance(state, target))
        visited = []

        while not open.isEmpty():
            current = open.pop()
            if current[0] == target:
                return current[1]
            visited.append(current[0])
            x = [-1, 0, 1, 0]
            y = [0, 1, 0, -1]
            for i in range(4):
                node = (current[0][0] + x[i], current[0][1] + y[i])
                if node not in visited and node not in closed and node[0] > 0 and node[1] > 0 and node[0] < width and node[
                    1] < height:
                    open.push((node, current[1] + [node]), self.getMazeDistance(node, target))

        return []
