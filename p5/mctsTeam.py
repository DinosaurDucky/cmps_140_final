# myTeam.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

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

    return positions


def fixState(gameState, index, enemyIndices):

    #self.gameState = gameState
    pos = gameState.getAgentPosition(index)
    positions = []
    for playerIndex in range(gameState.getNumAgents()):
        if playerIndex in enemyIndices:
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
        self.playerJustMoved = (self.index - 1) % state.getNumAgents() # not sure what this is for yet

    def UCTSelectChild(self):
        # ucb1 formula to select a child node
        # balances exploitation vs exploration
        s = sorted(self.childNodes, key = lambda c: c.scoreSum/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        #s = random.shuffle(self.childNodes);
        return s

    def addChild(self, move, state, index):
        newNode = Node(move=move, parent=self, state=state, index=index)
        self.untriedMoves.remove(move)
        self.childNodes.append(newNode)
        return newNode

    def update(self, score):
        self.visits += 1
        self.scoreSum += score


def UCT(rootState, maxIterations, index, enemyIndices ):
    fixedState = fixState(rootState, index, enemyIndices)
    rootNode = Node(state = fixedState)


    for i in range(maxIterations):
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
            legalActions = state.getLegalActions(index % state.getNumAgents())
            state = state.generateSuccessor(index % state.getNumAgents(), random.choice(legalActions))
            index += 1
            count += 1

        #backpropagate
        while node:
            node.update(state.getScore())
            node = node.parentNode  
            
    return sorted(rootNode.childNodes, key = lambda c: c.visits)[-1].move # return the move that was most visited
          
            
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


  def chooseAction(self, gameState):
 

    return UCT(gameState, 100, self.index, self.getOpponents(gameState) )

