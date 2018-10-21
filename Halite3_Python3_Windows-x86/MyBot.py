#!/usr/bin/env python3
# Python 3.6

# Import the Halite SDK, which will let you interact with the game.
import hlt
from hlt import constants
from hlt import Direction
from hlt import Position
import random
import logging

""" <<<Game Begin>>> """


game = hlt.Game()
# At this point "game" variable is populated with initial map data.
# This is a good place to do computationally expensive start-up pre-processing.
# As soon as you call "ready" function below, the 2 second per turn timer will start.

ship_status = {}
stuck_cnt = {}

game.ready("MyPyth0n80t")
logging.info("Successfully created bot! My Player ID is {}.".format(game.my_id))

""" <<<Game Loop>>> """

#logging.info('Directions: {} {} {} {} {}'.format(Direction.Still, Direction.North,Direction.South,Direction.East,Direction.West))

greedy = 10

while True:
    game.update_frame()
    me = game.me
    game_map = game.game_map
    
    command_queue = []
    to_be_occupied_pos = {}

    # command_queue.append(ship.make_dropoff())
    # me.get_dropoffs()
    # game_map.calculate_distance(ship.position, dropoff.position)
    
    # preprocess: ship that cannot move
    for ship in me.get_ships():
        if ship.id not in stuck_cnt:
            stuck_cnt[ship.id] = 0
        if game_map[ship.position].halite_amount / 10 > ship.halite_amount:
            move = Direction.Still
            command_queue.append(ship.move(move))
            
            to_be_occupied_pos[(ship.position.x, ship.position.y)] = True
            stuck_cnt[ship.id] += 1
        else:
            command_queue.append('TBD')
            
    cnt = -1;
    
    for ship in me.get_ships():

        cnt += 1
        
        if command_queue[cnt] != 'TBD':
            continue
        
        # update status        
        if ship.id not in ship_status or ship.position == me.shipyard.position:
            ship_status[ship.id] = "exploring"
        if ship.halite_amount >= constants.MAX_HALITE * 0.8:
            ship_status[ship.id] = "returning"            

        
        if game.turn_number >= 200:
            logging.info("Ship {} has {} halite.".format(ship.id, ship.halite_amount)) 
            logging.info("Current ship position: {}".format(ship.position))
            logging.info(ship_status[ship.id])
        
        # make a move
        #returning ships
        
        
        if ship_status[ship.id] == "returning":
            if (game_map[ship.position].halite_amount > constants.MAX_HALITE / greedy and not ship.is_full) \
            or game_map[ship.position].halite_amount / 10 > ship.halite_amount:
                move = Direction.Still
            else:
                move = game_map.naive_navigate(ship, me.shipyard.position)
        else: # exploring ships
            if (game_map[ship.position].halite_amount > constants.MAX_HALITE / greedy and not ship.is_full) \
            or game_map[ship.position].halite_amount / 10 > ship.halite_amount:
                move = Direction.Still
            else:
                best_x = ship.position.x
                best_y = ship.position.y
                maxHLT = 0;
                
                search_len = 6
                
                for i in range(-search_len, search_len + 1):
                    for j in range(-search_len, search_len + 1):
                        curr_x = ship.position.x + i
                        curr_y = ship.position.y + j
                        if game_map[Position(curr_x, curr_y)].halite_amount > maxHLT:
                            maxHLT = game_map[Position(curr_x, curr_y)].halite_amount
                            best_x = curr_x
                            best_y = curr_y
                            
                move = game_map.naive_navigate(ship, Position(best_x, best_y))
                # if ship.position == me.shipyard.position:
                #     move = random.choice(Direction.get_all_cardinals())
                for current_direction in Direction.get_all_cardinals():
                    pos = ship.position.directional_offset(current_direction)
                    if game_map[pos].halite_amount > constants.MAX_HALITE / greedy:
                        move = current_direction
        
        if stuck_cnt[ship.id] > 5:
            move = random.choice(Direction.get_all_cardinals())
        
        if game.turn_number >= 200:
            logging.info('best_x is {}, best_y is {}'.format(best_x, best_y)) 
            logging.info('optimal_move is {}'.format(move)) 
        
        # Direction.West, Direction.North, Direction.East, Direction.South
        # avoid collapse  
        if move == Direction.Still:
            # logging.info('optimal_move is {}'.format(move))
            target = ship.position
        else:
            # logging.info('optimal_move is {}'.format(move))
            target = ship.position.directional_offset(move)
            
        if (target.x, target.y) in to_be_occupied_pos:
            for optional_direction in ([random.choice(Direction.get_all_cardinals())] + [Direction.Still] + Direction.get_all_cardinals()):
                optional_target = ship.position.directional_offset(optional_direction)
                if (optional_target.x, optional_target.y) not in to_be_occupied_pos:
                    move = optional_direction
                    break;
                    
        if game.turn_number >= 200:
            logging.info('modified_move is {}'.format(move))      
        target = ship.position.directional_offset(move)        
        to_be_occupied_pos[(target.x, target.y)] = True;
        command_queue[cnt] = ship.move(move)
        
        if move == Direction.Still:
            stuck_cnt[ship.id] += 1
        else:
            stuck_cnt[ship.id] = 0
        
    if game.turn_number <= constants.MAX_TURNS - 200 and me.halite_amount >= constants.SHIP_COST \
    and not game_map[me.shipyard].is_occupied and (me.shipyard.position.x, me.shipyard.position.y) not in to_be_occupied_pos:
        command_queue.append(game.me.shipyard.spawn())

    
    game.end_turn(command_queue)


