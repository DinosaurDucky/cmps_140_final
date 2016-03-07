# myTeam.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

import time
from captureAgents import CaptureAgent
import random, time, util
from distanceCalculator import Distancer
from game import Directions
from game import AgentState
from game import Configuration
from capture import GameState
from math import *


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'MCTSAgent', second = 'MCTSAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########


def inverseManhattanDistance(pos, distance, gameState):
    x, y = pos
    width = gameState.data.layout.width
    height = gameState.data.layout.height
    positions = []
    testCount = 0
    originalDist = distance
    while len(positions) is 0:
        for i in range(distance):
            targetX = x - distance + i
            targetY = y + i
            if 1 <= targetX and targetX < width and 1 <= targetY and targetY < height and not gameState.hasWall(targetX, targetY):
                positions.append((targetX, targetY))
        for i in range(distance):
            targetX = x + distance - i
            targetY = y + i
            if 1 <= targetX and targetX < width and 1 <= targetY and targetY < height and not gameState.hasWall(targetX, targetY):
                positions.append((targetX, targetY))

        for i in range(1, distance):
            targetX = x - distance + i
            targetY = y - i
            if 1 <= targetX and targetX < width and 1 <= targetY and targetY < height and not gameState.hasWall(targetX, targetY):
                positions.append((targetX, targetY))
        for i in range(1, distance):
            targetX = x + distance - i
            targetY = y - i
            if 1 <= targetX and targetX < width and 1 <= targetY and targetY < height and not gameState.hasWall(targetX, targetY):
                positions.append((targetX, targetY))

        distance -= 1
        if distance < 0:
            distance = 5
    return positions


def fixState(gameState, index, enemyIndices):

    #self.gameState = gameState
    pos = gameState.getAgentPosition(index)
    positions = []
    for playerIndex in range(gameState.getNumAgents()):
        if playerIndex in enemyIndices:

            if gameState.getAgentPosition(playerIndex):
                positions.append( gameState.getAgentPosition(playerIndex))

            else:
                dist = gameState.getAgentDistances()[playerIndex]
                enemyPositions = inverseManhattanDistance(pos, dist, gameState)
                #can put nonrandom choice here
                positions.append(random.choice(enemyPositions))
        else:
            positions.append( gameState.getAgentPosition(playerIndex))

    for i in range(gameState.getNumAgents()):
        if gameState.data.agentStates[i].configuration is None:
            isPacman = i%2 == 1 and gameState.isRed(positions[i]) or i % 2 == 0 and not gameState.isRed(positions[i])
            gameState.data.agentStates[i] = AgentState(Configuration(positions[i], 'Stop'), isPacman)


    return gameState

class Node:
    def __init__(self, move = None, parent = None, state = None, index = 0):
        self.move = move # the move that got us to this node
        self.state = state
        self.parentNode = parent
        self.childNodes = []
        self.scoreSum = 0
        self.visits = 0
        self.index = index
        self.untriedMoves = self.state.getLegalActions(self.index)
        self.untriedMoves.remove("Stop")

    def UCTSelectChild(self):
        # ucb1 formula to select a child node
        # balances exploitation vs exploration
        #s = sorted(self.childNodes, key = lambda c: c.scoreSum/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        s = max(self.childNodes, key = lambda c: c.scoreSum/c.visits + 2*log(self.visits)/c.visits)
        #s = sorted(self.childNodes, key = lambda c: c.scoreSum*c.scoreSum/(c.visits*c.visits) + 2*log(self.visits)/c.visits)[-1]
        #s = max(self.childNodes, key = lambda c: c.scoreSum*c.scoreSum/(c.visits*c.visits) + 2*log(self.visits)/c.visits)

        return s

    def addChild(self, move, state, index):
        newNode = Node(move=move, parent=self, state=state, index=index)
        self.untriedMoves.remove(move)
        self.childNodes.append(newNode)
        return newNode

    def update(self, score):
        self.visits += 1
        self.scoreSum += score
        
    def __repr__(self):
        return "[M:" + str(self.move) + " W/V:" + str(self.scoreSum) + "/" + str(self.visits) + " U:" + str(self.untriedMoves) + "] index: " + str(self.index)

    def TreeToString(self, indent):
        s = self.IndentString(indent) + str(self)
        for c in self.childNodes:
             s += c.TreeToString(indent+1)
        return s

    def IndentString(self,indent):
        s = "\n"
        for i in range (1,indent+1):
            s += "| "
        return s

    def ChildrenToString(self):
        s = ""
        for c in self.childNodes:
             s += str(c) + "\n"
        return s   



          
            
class MCTSAgent(CaptureAgent):
    """
    A Dummy agent to serve as an example of the necessary agent structure.
    You should look at baselineTeam.py for more details about how to
    create an agent as this is the bare minimum.
    """

    def registerInitialState(self, gameState):
        """
        This method handles the initial setup of the
        agent to populate useful fields (such as what team
        we're on).
    
        A distanceCalculator instance caches the maze distances
        between each pair of positions, so your agents can use:
        self.distancer.getDistance(p1, p2)
    
        IMPORTANT: This method may run for at most 15 seconds.
        """
    
        '''
        Make sure you do not delete the following line. If you would like to
        use Manhattan distances instead of maze distances in order to save
        on initialization time, please take a look at
        CaptureAgent.registerInitialState in captureAgents.py.
        '''
        CaptureAgent.registerInitialState(self, gameState)

    '''
    Your initialization code goes here, if you need any.
    '''

    def UCT(self, rootState, index, enemyIndices ):
        fixedState = fixState(rootState, index, enemyIndices)
        rootNode = Node(state = fixedState, index=index)
        timeout = time.time() + .98
        counter = 0

        while time.time() < timeout:
            counter += 1

            node = rootNode
            state = GameState(node.state)
            index = node.index

   	
            #select
            while not node.untriedMoves and node.childNodes:
                node = node.UCTSelectChild()
                state = state.generateSuccessor(index % state.getNumAgents(), node.move)
                index += 1

            #expand
            if node.untriedMoves:
                move = random.choice(node.untriedMoves)
                state = state.generateSuccessor(index % state.getNumAgents(), move)
                node = node.addChild(move, state, (index+1) % state.getNumAgents() )

            count = 0
            #rollout
            while count < 10 and state.getLegalActions(index % state.getNumAgents()):
                #if index == (self.index + 2) % state.getNumAgents():
                #    index += 1
                legalActions = state.getLegalActions(index % state.getNumAgents())
                state = state.generateSuccessor(index % state.getNumAgents(), random.choice(legalActions))

                index += 1
                count += 1

            #backpropagate
            evaluation = self.evaluate(state)
            while node:
                node.update(evaluation)
                node = node.parentNode

        print "iterated ", counter, " times"

        return max(rootNode.childNodes, key = lambda c: c.visits).move # return the move that was most visited


    def evaluate(self, gameState):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState)
        weights = self.getWeights(gameState)

        return features * weights

    def getFeatures(self, gameState):
        features = util.Counter()
        features['gameStateScore'] = self.getScore(gameState)

        # Compute distance to the nearest food
        myPos = gameState.getAgentState(self.index).getPosition()
        enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
        
        # Compute distance to the nearest food     
        foodList = self.getFood(gameState).asList()
        if len(foodList) > 0: # This should always be True,  but better safe than sorry
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            features['distanceToFood'] = minDistance
            
        # Compute distance to the nearest capsule      
        for a in enemies:
            if a.getPosition() != None:
                capList = self.getCapsules(gameState)
                if len(capList) > 0: # This should always be True,  but better safe than sorry
                    minDistance = min([self.getMazeDistance(myPos, cap) for cap in capList])
                    features['distanceToCapsules'] = minDistance


        # encourage the agents to spread out
        teamMateIndex = (self.index + 2) % gameState.getNumAgents()
        teamMatePos = gameState.getAgentPosition(teamMateIndex)
        teamMateDistance = self.getMazeDistance(myPos, teamMatePos)
        features['teamMateDistance'] = teamMateDistance
        
        #finds list of enemies that are currently invading and chase them unless scared
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        if len(invaders) > 0:
            dists = []
            for a in invaders:
                dists.append( self.getMazeDistance(myPos, a.getPosition()) )
                if gameState.getAgentState(self.index).scaredTimer > 0:
                    dists[-1] *= -1
            features['invaderDistance'] = min(dists)

        #finds list of enemies that are currently defending and kite them unless scared        
        defenders = [a for a in enemies if not a.isPacman and a.getPosition() != None]
        if len(defenders) > 0:
            dists = []
            for a in defenders:
                dists.append(self.getMazeDistance(myPos, a.getPosition()))
                if a.scaredTimer > 0:
                    dists[-1] *= -1
            features['defenderDistance'] = min(dists)


        return features

    def getWeights(self, gameState):
        return {'gameStateScore': 1.5, 'distanceToFood': -.2, 'distanceToCapsules':-.5, \
        'teamMateDistance': .1, 'invaderDistance': -.1, 'defenderDistance': .1}


    def chooseAction(self, gameState):
    
        return self.UCT(gameState, self.index, self.getOpponents(gameState) )
