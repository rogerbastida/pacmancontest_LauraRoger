# baselineTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# baselineTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html

import random
import util

from captureAgents import CaptureAgent
from game import Directions
from util import nearestPoint

import capture


#################
# Team creation #
#################

def create_team(first_index, second_index, is_red,
                first='OffensiveReflexAgent', second='DefensiveReflexAgent', num_training=0):
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
    return [eval(first)(first_index), eval(second)(second_index)]


##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
    """
    A base class for reflex agents that choose score-maximizing actions
    """

    def __init__(self, index, time_for_computing=.1):
        super().__init__(index, time_for_computing)
        self.start = None

    def register_initial_state(self, game_state):
        self.start = game_state.get_agent_position(self.index)
        CaptureAgent.register_initial_state(self, game_state)

    def choose_action(self, game_state):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = game_state.get_legal_actions(self.index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(game_state, a) for a in actions]
        # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

        max_value = max(values)
        best_actions = [a for a, v in zip(actions, values) if v == max_value]

        food_left = len(self.get_food(game_state).as_list())

        if food_left <= 2:
            best_dist = 9999
            best_action = None
            for action in actions:
                successor = self.get_successor(game_state, action)
                pos2 = successor.get_agent_position(self.index)
                dist = self.get_maze_distance(self.start, pos2)
                if dist < best_dist:
                    best_action = action
                    best_dist = dist
            return best_action

        return random.choice(best_actions)

    def get_successor(self, game_state, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = game_state.generate_successor(self.index, action)
        pos = successor.get_agent_state(self.index).get_position()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generate_successor(self.index, action)
        else:
            return successor

    def evaluate(self, game_state, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.get_features(game_state, action)
        weights = self.get_weights(game_state, action)
        return features * weights

    def get_features(self, game_state, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = self.get_successor(game_state, action)
        features['successor_score'] = self.get_score(successor)
        return features

    def get_weights(self, game_state, action):
        """
        Normally, weights do not depend on the game state.  They can be either
        a counter or a dictionary.
        """
        return {'successor_score': 1.0}


class OffensiveReflexAgent(ReflexCaptureAgent):
    """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
    #Features:
        #Successor_score -> Quants foods queden per menjar (no entregats) #20
        #distance_to_fod -> distancia al food m??s proper
        #distance_to_ghost -> distancia del pacman al ghost
        #ghost_state -> El ghost espantat o no espantat

    def get_features(self, game_state, action):
        features = util.Counter()
        successor = self.get_successor(game_state, action) #successorgamestate
        food_list = self.get_food(successor).as_list()
        capsules_list = self.get_capsules(successor)
        defend_food_list = self.get_food_you_are_defending(successor).as_list()
        my_state = successor.get_agent_state(self.index)
        my_pos = successor.get_agent_state(self.index).get_position()
        features['successor_score'] = -len(food_list)  # 1) Eaten food

        # 2) Compute distance to the nearest food
        if len(food_list) > 0:  # This should always be True,  but better safe than sorry
            min_distance = min([self.get_maze_distance(my_pos, food) for food in food_list])
            if min_distance < 3:
                features['distance_to_food'] = min_distance
            elif min_distance < 7:
                features['distance_to_food'] = min_distance * 0.8
            else:
                features['distance_to_food'] = min_distance * 0.4

        # 3) Num of ghosts
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        ghosts = [a for a in enemies if not a.is_pacman and a.get_position() is not None]
        features['num_ghosts'] = len(ghosts)
        #4) Distance to ghosts
        if len(ghosts) > 0:
            dists = [self.get_maze_distance(my_pos, a.get_position()) for a in ghosts]
            ghost_dist = min(dists)
            if ghost_dist < 5:
                features['ghosts_distance'] = min(dists)
            elif ghost_dist < 8:
                features['ghosts_distance'] = min(dists) * 0.7
            else:
                features['ghosts_distance'] = min(dists) * 0.3


        # 5) stop
        if action == Directions.STOP: features['stop'] = 1
        
        # 6) reverse
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev:
            features['reverse'] = 1

        

        # 7) eaten_food * dist_to_home
        #eaten_food
        #initial_food_eat = self.register_initial_state(game_state).get_food()
        #initial_food_defend = self.register_initial_state.get_food_you_are_defending()
        
        initial_food_eat = 20
        initial_food_defend = 20
        

        myfood_eaten = initial_food_defend - len(defend_food_list)

        current_eaten_food = initial_food_eat + initial_food_defend - myfood_eaten - len(food_list) - len(defend_food_list) - self.get_score(successor) #Food eaten and not saved

        #dist_to_home
        '''
        #primitve_dist_to_home
        dist = 100000
        for pos in defend_food_list:
            dist = min(self.get_maze_distance(my_pos, pos), dist)
        dist_to_home = dist
        '''
        half_width = successor.data.layout.width // 2
        height = successor.data.layout.height
        if self.red: #Determine my half of the grid and know the frontier
            i = half_width - 1
        else:
            i = half_width + 1
        
        l_pos = []
        for j in range(height):
            l_pos.append((i,j))
        
        validPositions = []
        for i in l_pos:
            if not successor.has_wall(i[0], i[1]): #If the position has a wall we don't consider it
                validPositions.append(i)

        dist = 100000
        for validPosition in validPositions:
            dist = min(self.get_maze_distance(my_pos, validPosition), dist)
        dist_to_home = dist
        
        features['eaten_foodxdist_to_home'] = current_eaten_food * dist_to_home

        # 8) Score
        features['score'] = self.get_score(successor) 

        # 9) Scared_ghosts
        for ghost in ghosts:
            if ghost.scared_timer > 5:
                features['ghosts_distance'] = - features['ghosts_distance']/8 #Kill ghosts
                features['successor_score'] = features['successor_score'] * 3 #Eat a lot of food
                features['eaten_foodxdist_to_home'] = 0 #So it do not return home

        # 10)Capsules
        if len(capsules_list) > 0:
            min_distance = min([self.get_maze_distance(my_pos, capsule) for capsule in capsules_list])
            features['distance_to_capsule'] = min_distance
        
        # 11) successor_capsules
        features['successor_capsules'] = -len(capsules_list)

        # 12) Kill in my_field
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        invaders = [a for a in enemies if a.is_pacman and a.get_position() is not None]
        if len(invaders) > 0:
            dists = [self.get_maze_distance(my_pos, a.get_position()) for a in invaders]
            enemy_dist = min(dists)
            if not my_state.is_pacman or enemy_dist < 5:
                features['invader_distance'] = enemy_dist

        return features

    def get_weights(self, game_state, action):
        return {'successor_score': 200, 'distance_to_food': -6, 'ghosts_distance': 600, 'stop': -100, 'reverse': -5, 'eaten_foodxdist_to_home': -4, 'score':100, 'distance_to_capsule': -5, 'successor_capsules': 40, 'invader_distance': -20}


class DefensiveReflexAgent(ReflexCaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def get_features(self, game_state, action):
        features = util.Counter()
        successor = self.get_successor(game_state, action)
        food_to_protect_list = self.get_food_you_are_defending(successor).as_list()
        capsules_to_protect_list = self.get_capsules_you_are_defending(successor)
        my_state = successor.get_agent_state(self.index)
        my_pos = my_state.get_position()

        # 1) on_defense Computes whether we're on defense (1) or offense (0)
        features['on_defense'] = 1
        if my_state.is_pacman: features['on_defense'] = 0

        # 2) num_invaders Computes distance to invaders we can see
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        invaders = [a for a in enemies if a.is_pacman and a.get_position() is not None]
        features['num_invaders'] = len(invaders)
        # 3) invader distance
        if len(invaders) > 0:
            dists = [self.get_maze_distance(my_pos, a.get_position()) for a in invaders]
            features['invader_distance'] = min(dists)
        # 4) Stop
        if action == Directions.STOP: features['stop'] = 1
        # 5) Reverse
        rev = Directions.REVERSE[game_state.get_agent_state(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1
        
        # 6) we_scared (if we are scares, then we run away the pacman)
        team_agents = [successor.get_agent_state(i) for i in self.get_team(successor)]
        our_ghosts = [a for a in team_agents if not a.is_pacman and a.get_position() is not None]
        for ghost in our_ghosts:
            if ghost.scared_timer > 0:
                if features['invader_distance'] < 4:
                    features['invader_distance'] = -features['invader_distance']
                elif features['invader_distance'] < 7: 
                    features['invader_distance'] = -features['invader_distance'] * 0.7
                else:
                    features['invader_distance'] = -features['invader_distance'] * 0.3

        # 7) distance to our food (avg) (for camping our food)
        if len(food_to_protect_list) > 0:  # This should always be True,  but better safe than sorry
            distances = ([self.get_maze_distance(my_pos, food) for food in food_to_protect_list])
            avg_distance = sum(distances)/len(distances)
            features['distance_to_our_food'] = avg_distance
        
        # 8) random_factor (to get some random moves)
        features['random_factor'] = random.random() #util.flipCoin(0.5)

        # 9) dist_to_frontier (as the other team will enter from the frontier)
        half_width = successor.data.layout.width // 2
        height = successor.data.layout.height
        if self.red: #Determine my half of the grid and know the frontier
            i = half_width - 1
        else:
            i = half_width + 1
        
        l_pos = []
        for j in range(height):
            l_pos.append((i,j))
        
        validPositions = []
        for i in l_pos:
            if not successor.has_wall(i[0], i[1]): #If the position has a wall we don't consider it
                validPositions.append(i)

        dist = 100000
        for validPosition in validPositions:
            dist = min(self.get_maze_distance(my_pos, validPosition), dist)
        dist_to_home = dist
        features['dist_to_frontier'] = dist_to_home

        # 10) dist_from_other_agent (avoiding both agents to be very close so they can look more terrain)
        team_agents = [successor.get_agent_state(i) for i in self.get_team(successor)] #I know i have it on top
        our_agents = [a for a in team_agents if a.get_position() is not None] #I know it's the sam
        agent_distance = -10000
        for agent in our_agents:
            agent_distance = max(self.get_maze_distance(my_pos, agent.get_position()), agent_distance)
        if agent_distance < 4:
            features['dist_from_other_agent'] = agent_distance
        elif agent_distance < 7:
            features['dist_from_other_agent'] = agent_distance * 0.6
        else:
            features['dist_from_other_agent'] = agent_distance * 0.3

        
        # 11) min_dist_from_all_enemies
        enemies = [successor.get_agent_state(i) for i in self.get_opponents(successor)]
        invaders = [a for a in enemies if a.get_position() is not None]
        distancia = []
        if len(invaders) > 0:
            distancia = [self.get_maze_distance(my_pos, a.get_position()) for a in invaders]
            if min(distancia) < 3:
                features['min_dist_from_all_enemies'] = min(distancia)
            elif min(distancia) < 6:
                features['min_dist_from_all_enemies'] = min(distancia) * 0.5
            else:
                features['min_dist_from_all_enemies'] = min(distancia) * 0.3
        # 12) max_dist_from_all_enemies (the other one)
            if max(distancia) < 3:
                features['max_dist_from_all_enemies'] = max(distancia)
            elif max(distancia) < 6:
                features['max_dist_from_all_enemies'] = max(distancia) * 0.5
            else:
                features['max_dist_from_all_enemies'] = max(distancia) * 0.3
        
        return features
    
    def get_weights(self, game_state, action):
        return {'num_invaders': -1000, 'on_defense': 100, 'invader_distance': -15, 'stop': -100, 'reverse': -2, 'distance_to_our_food': -1, 'random_factor': -0.7, 'dist_to_frontier': -0.3, 'dist_from_other_agent': 0.2, 'min_dist_from_all_enemies': -5, 'max_dist_from_all_enemies': -1}

