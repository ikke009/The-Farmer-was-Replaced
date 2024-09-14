#Ex-situ BFS solver algorithm
#Initiates the algorithm by first following the left wall, by doing so creating a moveset that passes over each tile at least once
#From ths moveset a map of the maze is inferred, this map can then be used to find the shortest path to the treasure without having to move the drone
#Every so often, the map of the maze is updated to find any walls that were removed, thus enabling faster paths to be found

#Downside: The pathfinding algorithm becomes the speed bottleneck, as it can sometimes take a second or so to find the fastest path

def better_mazeloop(iterations):
    if iterations > 300:
        iterations = 300
        
    def reverse_direction(direction):
        if direction == North:
            return South
        if direction == South:
            return North
        if direction == East:
            return West
        if direction == West:
            return East
            
    #initiate new maze
    clear()
    move_home()
    make_soil()
    plant(Entities.Bush)
    while get_entity_type() == Entities.Bush:
        use_item(Items.Fertilizer)
    
    #follow left wall to find the moveset starting from and ending at (0,0), write moveset to variable
    #simultaniously, keep track of when the treasure is passed and note the coordinates
    def generate_moveset(): 
        directions = [North, East, South, West]
        face = 0
        moveset = []
        treasure_location = (0, 0)
        
        def rr(face=face):
            return (face+1)%4
        
        def rl(face=face):
            return (face-1)%4
        
        def forward(directions = directions, face = face):
            return move(directions[face])
        
        coordscheck = {}
        while (len(coordscheck) < (get_world_size()**2)) or ((get_pos_x(), get_pos_y()) != (0, 0)):
            try_move = forward()
            if try_move == True:
                moveset.append(directions[face])
                coordscheck[(get_pos_x(), get_pos_y())] = 1
                if get_entity_type() == Entities.Treasure:
                    treasure_location = (get_pos_x(), get_pos_y())
            while not try_move:
                face = rr()
                try_move = forward()
                if try_move == True:
                    moveset.append(directions[face])
                    coordscheck[(get_pos_x(), get_pos_y())] = 1
                    if get_entity_type() == Entities.Treasure:
                        treasure_location = (get_pos_x(), get_pos_y())
            face = rl()
        return moveset, treasure_location

    #deduce from moveset where the walls are on each coordinate
    #from this, make mazemap dictionary {(x, y): {North, West}} for example
    moveset, treasure_location = generate_moveset()
    
    def generate_mazemap(moveset):
        def lefthand(direction):
            if direction == North:
                return West
            if direction == East:
                return North
            if direction == South:
                return East
            if direction == West:
                return South
        
        directions = {
            North: (0, 1),
            East: (1, 0),
            South: (0, -1),
            West: (-1, 0)
        }
        mazemap = {}
        for x in range(get_world_size()):
            for y in range(get_world_size()):
                mazemap[x, y] = set()
                
        current_coordinates = (0, 0)
        for i in range(len(moveset)):
            current_walls = set()
            if current_coordinates == (0,0):
                current_walls.add(South)
                current_walls.add(West)
            current_move = moveset[i]
            while lefthand(current_move) != reverse_direction(moveset[i-1]):
                current_walls.add(lefthand(current_move))
                current_move = lefthand(current_move)
            x, y = current_coordinates
            mapvalue = mazemap[x, y]
            for wall in current_walls:
                mapvalue.add(wall)
            mazemap[x, y] = mapvalue
            dx, dy = directions[moveset[i]]
            current_coordinates = (x+dx, y+dy)
        
        return mazemap
    
    mazemap = generate_mazemap(moveset)

    #bfs solver finds shortest path to target coordinates, using mazemap for ex-situ execution 
    def BFS_solver(goal, mazemap):
        directions = {
            North: (0, 1),
            East: (1, 0),
            South: (0, -1),
            West: (-1, 0)
        }
    
        start = (get_pos_x(), get_pos_y())
        solution = []
        frontier = [start]
        visited = {start: None}
    
        while frontier:
            selected_node = frontier.pop(0)
            if selected_node == goal:
                break
    
            for direction in directions:
                dx, dy = directions[direction]
                new_x, new_y = selected_node[0] + dx, selected_node[1] + dy
                neighbour = (new_x, new_y)
    
                # Check if the selected node exists in mazemap
                if selected_node in mazemap:
                    walls = mazemap[selected_node]
                else:
                    walls = set()
    
                if (0 <= new_x < get_world_size()) and (0 <= new_y < get_world_size()) and neighbour not in visited:
                    if direction not in walls:  # No wall in the direction we're trying to go
                        frontier.append(neighbour)
                        visited[neighbour] = selected_node
        path = []
        current_node = goal
        while current_node != start:
            prev_node = visited[current_node]
            if prev_node[0] < current_node[0]:
                path.append(East)
            elif prev_node[0] > current_node[0]:
                path.append(West)
            elif prev_node[1] < current_node[1]:
                path.append(North)
            elif prev_node[1] > current_node[1]:
                path.append(South)
            current_node = prev_node
    
        return path[::-1]
    
    def update_mazemap(mazemap, moveset):
        mazemap = mazemap
        directions = {
            North: (0, 1),
            East: (1, 0),
            South: (0, -1),
            West: (-1, 0)
        }
        path = BFS_solver((0,0), mazemap)
        for i in path:
            move(i)
        visited = set()
        for i in moveset:
            cur_x, cur_y = get_pos_x(), get_pos_y()
            cur_walls = mazemap[cur_x, cur_y]
            for direction in cur_walls:
                missing_walls = []
                if move(direction):
                    move(reverse_direction(direction))
                    missing_walls.append(direction)
            for j in missing_walls:
                if j in cur_walls:
                    cur_walls.remove(j)
            mazemap[cur_x, cur_y] = cur_walls
            move(i)
        return mazemap
        
    for iteration in range(iterations):
        path = BFS_solver(treasure_location, mazemap)
        for i in path:
            move(i)
            treasure_location = measure()
            while get_entity_type() == Entities.Treasure:
                use_item(Items.Fertilizer)
        if iteration in [10, 20, 40, 80, 100, 150, 200]:
            mazemap = update_mazemap(mazemap, moveset)
    harvest()
