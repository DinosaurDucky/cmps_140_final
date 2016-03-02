# myTeam.py
# ---------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
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
        #s = sorted(self.childNodes, key = lambda c: c.currentEval/c.visits + sqrt(2*log(self.visits)/c.visits))[-1]
        s = random.shuffle(self.childNodes);
        return s

    def addChild(self, move, state, index):
        newNode = Node(move=move, parent=self, state=state, index=index)
        self.untriedMoves.remove(move)
        self.childNodes.append(newNode)
        return newNode

    def update(self, score):
        self.visits += 1
        self.scoreSum += score

def UCT(rootState, maxIterations=100):
    rootNode = Node(state = rootState)

    for i in range(maxIterations):
        node = rootNode
        state = GameState(node.state)
        index = node.index

        #select:
        while not node.untriedMoves and node.childNodes:
            node = node.UCTSSelectChild()
            state = state.generateSuccessor(index, move)
            index += 1
            
        #expand
        if node.untriedMoves:
            move = random.choice(node.untriedMoves)
            state = state.generateSuccessor(index, move)
            node = node.addChild(move, state, (index+1) % state.getNumAgents() )
            
        #rollout
        while state.GetMoves():
            legalActions = state.getLegalActions(index % state.getNumAgents())
            state = getSuccessor(state, random.choice(legalActions))
            index += 1
        
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
 
    
    return UCT(gameState, 100)

