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
        mypos = gameState.getAgentPosition(self.index)

        if self.getPreviousObservation() is not None:
            if self.getPreviousObservation().hasFood(mypos[0], mypos[1]):
                self.eaten += 1

        nearestFood = self.nearestFood(gameState)
        nearestEnemy = self.getNearestEnemy(gameState)

        if not gameState.getAgentState(self.index).isPacman:
            self.eaten = 0
            while len(self.plan[0]) == 0:
                y = random.choice(range(0, self.height, 1))
                if not gameState.hasWall(int(self.width / 2), y):
                    self.plan = [[int(self.width / 2) + 1, y],
                                 self.bfs(gameState, self.width, self.height, nearestEnemy,
                                          [int(self.width / 2), y])]
            if len(self.plan[1]) == 0:
                if not len(self.plan[0]) == 0:
                    self.plan[1] = self.bfs(gameState, self.width, self.height, nearestEnemy, self.plan[0])
            self.escapepath = self.plan[1]
        else:
            self.plan = [[], []]
            if len(nearestEnemy) > 0:
                if nearestEnemy[1] < 4 :
                    self.escapepath = self.bfs(gameState, self.width, self.height, nearestEnemy, [self.width / 2 - 4])
            else:
                self.escapepath = []
                if self.eaten == 5:
                    self.escapepath = self.bfs(gameState, 36, 17, nearestEnemy, [self.width / 2 - 1])

        actions = gameState.getLegalActions(self.index)
        values = [self.evaluate(gameState, nearestFood, nearestEnemy, self.escapepath, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]

        action = random.choice(bestActions)
        return action

    def escapePath(self, game_state, width, height, enemy):

        stack = util.Stack()
        myState = game_state.getAgentState(self.index)
        myPos = myState.getPosition()

        visited = []
        if len(enemy) > 0:
            visited = [[enemy[0][0], enemy[0][1]]]
        stack.push([myPos[0], myPos[1]])
        path = []

        while not stack.isEmpty():

            myPos = [int(myPos[0]), int(myPos[1] + 0.5)]
            psize = len(visited)
            loop = []

            right = [myPos[0] - 1, myPos[1]]
            if right[0] >= 0 and right not in visited and not game_state.hasWall(right[0], right[1]):
                stack.push(right)
                visited.append(right)
            if right in visited: loop.append(right)

            up = [myPos[0], myPos[1] + 1]
            if up[1] < height and up not in visited and not game_state.hasWall(up[0], up[1]):
                stack.push(up)
                visited.append(up)
            if up in visited:  loop.append(up)

            down = [myPos[0], myPos[1] - 1]
            if down[1] >= 0 and down not in visited and not game_state.hasWall(down[0], down[1]):
                stack.push(down)
                visited.append(down)
            if down in visited: loop.append(down)

            left = [myPos[0] + 1, myPos[1]]
            if left[0] < width and left not in visited and not game_state.hasWall(left[0], left[1]):
                stack.push(left)
                visited.append(left)
            if left in visited: loop.append(left)

            if len(loop) > 0:
                for i in reversed(path):
                    if abs(i[0] - myPos[0]) + abs(i[1] - myPos[1]) > 1:
                        path.remove(i)
                    else:
                        break

            if myPos[0] == 1 and myPos[1] == 2:
                return path

            myPos = stack.pop()

            for i in reversed(path):
                if abs(i[0] - myPos[0]) + abs(i[1] - myPos[1]) > 1:
                    path.remove(i)
                else:
                    break
            path.append(myPos)
        return path

    def nearestFood(self, gameState):

        food = self.getFood(gameState).asList()
        distance = [self.getMazeDistance(gameState.getAgentPosition(self.index), a) for a in food]

        if len(food) < 3:
            previous = self.getFoodYouAreDefending(gameState).asList()[0]
            return [previous, self.getMazeDistance(gameState.getAgentPosition(self.index), previous)]
        nearestFood = food[0]
        nearestDstance = distance[0]

        for i in range(len(distance)):
            if distance[i] < nearestDstance:
                nearestFood = food[i]
                nearestDstance = distance[i]

        return [nearestFood, nearestDstance]

    def getNearestEnemy(self, gameState):
        myState = gameState.getAgentState(self.index)
        myPos = myState.getPosition()

        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        invaders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
        scare = 0
        if len(invaders) == 0:
            return []
        else:
            nearestEnemy = invaders[0].getPosition()
            isPacman = invaders[0].isPacman
            nearestDstance = dists[0]
            for i in range(len(dists)):
                if dists[i] < nearestDstance:
                    nearestEnemy = invaders[i].getPosition()
                    nearestDstance = dists[i]
                    scare = invaders[i].scaredTimer
        return [nearestEnemy, nearestDstance, scare, isPacman]

    def evaluate(self, gameState, nearestFood, nearestEnemy, escapepath, action):

        score = 0
        scorelist = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        next = gameState.generateSuccessor(self.index, action)
        nextpos = next.getAgentPosition(self.index)
        nextscore = next.getScore()

        if nextscore > gameState.getScore():
            score += 2
            scorelist[0] = 2
        if self.getMazeDistance(next.getAgentPosition(self.index), nearestFood[0]) < nearestFood[1]:
            score += 1
            scorelist[2] = 1

        pre = self.getPreviousObservation()
        if pre != None:
            if self.getPreviousObservation().getAgentPosition(self.index) == nextpos:
                score -= 5
                scorelist[3] = -5

        if len(nearestEnemy) > 0 and nearestEnemy[1] < 4:
            if next.getAgentState(self.index).isPacman:
                score += (self.getMazeDistance(next.getAgentPosition(self.index), nearestEnemy[0]) - nearestEnemy[1])
                scorelist[4] = (
                        self.getMazeDistance(next.getAgentPosition(self.index), nearestEnemy[0]) - nearestEnemy[1])
                nextActions = next.getLegalActions(self.index)
                if len(nextActions) == 2:
                    score -= 100
                    scorelist[5] = -100
        else:
            score += 2
            scorelist[6] = 2

        if len(escapepath) > 0:
            if [nextpos[0], nextpos[1]] in escapepath:
                if not (len(nearestEnemy) > 0 > nearestEnemy[2] and nearestEnemy[1] < 3):
                    score += 10
                    scorelist[7] = 10
        if action == Directions.STOP:
            score = -10
            scorelist[8] = -10

        return score

    def dfs(self, game_state, width, height, enemy):

        stack = util.Stack()
        myState = game_state.getAgentState(self.index)
        myPos = myState.getPosition()

        visited = []
        if len(enemy) > 0:
            visited = [[enemy[0][0], enemy[0][1]]]
        stack.push([myPos[0], myPos[1]])
        path = []

        while not stack.isEmpty():

            myPos = [int(myPos[0]), int(myPos[1] + 0.5)]
            psize = len(visited)
            loop = []

            right = [myPos[0] - 1, myPos[1]]
            if right[0] >= 0 and right not in visited and not game_state.hasWall(right[0], right[1]):
                stack.push(right)
                visited.append(right)
            if right in visited: loop.append(right)

            up = [myPos[0], myPos[1] + 1]
            if up[1] < height and up not in visited and not game_state.hasWall(up[0], up[1]):
                stack.push(up)
                visited.append(up)
            if up in visited:  loop.append(up)

            down = [myPos[0], myPos[1] - 1]
            if down[1] >= 0 and down not in visited and not game_state.hasWall(down[0], down[1]):
                stack.push(down)
                visited.append(down)
            if down in visited: loop.append(down)

            left = [myPos[0] + 1, myPos[1]]
            if left[0] < width and left not in visited and not game_state.hasWall(left[0], left[1]):
                stack.push(left)
                visited.append(left)
            if left in visited: loop.append(left)

            if len(loop) > 0:
                for i in reversed(path):
                    if abs(i[0] - myPos[0]) + abs(i[1] - myPos[1]) > 1:
                        path.remove(i)
                    else:
                        break

            if myPos[0] == 1 and myPos[1] == 2:
                return path

            myPos = stack.pop()

            for i in reversed(path):
                if abs(i[0] - myPos[0]) + abs(i[1] - myPos[1]) > 1:
                    path.remove(i)
                else:
                    break
            path.append(myPos)
        return path

    def bfs(self, game_state, width, height, enemy, point):

        queue = util.Queue()
        myState = game_state.getAgentState(self.index)
        myPos = myState.getPosition()

        visited = []
        if len(enemy) > 0:
            visited = [[enemy[0][0], enemy[0][1]]]
        queue.push([myPos[0], myPos[1]])

        path = []

        while not queue.isEmpty():

            myPos = [int(myPos[0]), int(myPos[1] + 0.5)]
            psize = len(visited)
            loop = []

            right = [myPos[0] - 1, myPos[1]]
            if right[0] >= 0 and right not in visited and not game_state.hasWall(right[0], right[1]):
                queue.push(right)
                visited.append(right)
            if right in visited: loop.append(right)

            up = [myPos[0], myPos[1] + 1]
            if up[1] < height and up not in visited and not game_state.hasWall(up[0], up[1]):
                queue.push(up)
                visited.append(up)
            if up in visited:  loop.append(up)

            down = [myPos[0], myPos[1] - 1]
            if down[1] >= 0 and down not in visited and not game_state.hasWall(down[0], down[1]):
                queue.push(down)
                visited.append(down)
            if down in visited: loop.append(down)

            left = [myPos[0] + 1, myPos[1]]
            if left[0] < width and left not in visited and not game_state.hasWall(left[0], left[1]):
                queue.push(left)
                visited.append(left)

            if left in visited: loop.append(left)
            myPos = queue.pop()
            path.append(myPos)

            if len(point) == 1:
                if myPos[0] == point[0]:
                    a = myPos
                    f = []
                    for i in reversed(path):
                        if abs(a[0] - i[0]) + abs(a[1] - i[1]) <= 1:
                            f.append(i)
                            a = i
                    return f
            else:

                if myPos[0] == point[0] and myPos[1] == point[1]:
                    a = myPos
                    f = []
                    for i in reversed(path):
                        if abs(a[0] - i[0]) + abs(a[1] - i[1]) <= 1:
                            f.append(i)
                            a = i
                    return f

        return []