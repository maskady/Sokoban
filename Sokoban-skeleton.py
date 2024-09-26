"""
@author: Florent Delalande 

This project is a Sokoban game in Python with Tkinter.
It was programmed as part of the PCO (Object-Oriented Design Project) course during my 2nd year at the University of Brest.

"""
import tkinter as tk
import tkinter.messagebox as tkMessageBox
import tkinter.simpledialog
from tkinter import messagebox

import os
import json

import sokobanXSBLevels
from enum import Enum

IMAGE_SIZE = 64
SCORE_FILE = "score.json"


"""
Direction:
    Useful for managing the calculation of positions for movements
"""
class Direction(Enum):
    Up = 1
    Down = 2
    Left = 3
    Right = 4

"""
Entity class represents a generic entity in the Sokoban game.
It is an abstract class that is inherited by other classes.
Attributes:
    image (tk.PhotoImage): A class attribute that holds the image representation of the entity.
Methods:
    __init__() -> None:
        Initializes a new instance of the Entity class.
    is_movable() -> bool:
        Determines if the entity can be moved.
    can_be_covered() -> bool:
        Determines if the entity can be covered by another entity.
    xsb_char() -> str:
        Returns the character representation of the entity for XSB (Sokoban) file format.
"""
class Entity(object):
    image: tk.PhotoImage = None
    
    def __init__(self) -> None:
        # It is an abstract method that is inherited by other classes.
        pass

    def is_movable(self) -> bool:
        # It is an abstract method that is inherited by other classes.
        pass

    def can_be_covered(self) -> bool:
        # It is an abstract method that is inherited by other classes.
        pass

    def xsb_char(self) -> str:
        # It is an abstract method that is inherited by other classes.
        pass

"""
Player:
    - storage of the score
    - incrementing the score
    - displaying the score
"""
class Player(object):
    def __init__(self, username, score) -> None:
        self.username = username
        self.score = score

    @classmethod
    def win(cls, username, level_num) -> None:
        cls.username = username
        current_score = cls.read_from_file(cls, username)
        if current_score is None or level_num > current_score:
            cls.score = level_num
        else:
            cls.score = current_score
        cls.write_to_file(cls)

    def write_to_file(self):
        f = open(os.path.join(os.path.dirname(__file__), SCORE_FILE),'r')
        data = json.load(f)
        f.close()
        data[self.username] = self.score
        f = open(os.path.join(os.path.dirname(__file__), SCORE_FILE),'w')
        json.dump(data,f)
        f.close()

    def read_from_file(self, username):
        f = open(os.path.join(os.path.dirname(__file__), SCORE_FILE),'r')
        data = json.load(f)
        f.close()
        if username in data:
            return data[username]
        else:
            return None

"""
    Players:
    - storage of Players
    - displaying Players

"""
class Players(object):
    @classmethod
    def read_from_file(cls):
        f = open(os.path.join(os.path.dirname(__file__), SCORE_FILE),'r')
        data = json.load(f)
        f.close()
        cls.player_list = []
        for username in data:
            cls.player_list.append(Player(username, data[username]))
        return cls.player_list

"""
Position:
    - storage of x and y coordinates,
    - verification of x and y in relation to a matrix
    - calculation of relative position from an offset and a direction 
"""
class Position(object):
    def __init__(self, x, y):
        self.x: int = x
        self.y: int = y

    def __str__(self):
        return 'Position(' + str(self.x) + ',' + str(self.y) + str(')') 

    def get_x(self):
        return self.x

    def get_y(self):
        return self.y

    # returns the position towards the direction #direction considering the offset
    #   Position(3,4).position_towards(Direction.Right, 2) == Position(5,4)
    def position_towards(self, direction: Direction, offset: int):
        new_pos = Position(self.x, self.y)
        match direction:
            case Direction.Left:
                new_pos.x -= offset
            case Direction.Up:
                new_pos.y -= offset
            case Direction.Right:
                new_pos.x += offset
            case Direction.Down:
                new_pos.y +=offset
        return new_pos

    # Returns True if the coordinates are valid in the warehouse
    def is_valid_in_wharehouse(self, wharehouse):
        return wharehouse.isPositionValid(self)

    # Converts the receiver to a corresponding position in a Canvas
    def as_canvas_position_in(self):
        lx = self.get_x() * IMAGE_SIZE
        ly = self.get_y() * IMAGE_SIZE
        return Position(lx, ly)

"""
WharehousePlan: Warehouse plan to store elements.
    The elements are stored in a matrix (#rawMatrix)
"""
class WharehousePlan(object):
    level_num = 0

    def __init__(self):
        pass

    def get_level_num(self):
        return self.level_num

    def get_mover(self):
        return self.mover

    @classmethod
    def from_xsb_matrix(cls, xsb_matrix,canvas):
        cls.staticMatrix: list[list[Entity]] = []
        cls.movableMatrix: list[list[Entity]] = []
        cls.canvas: tk.Canvas = canvas
        for line_idx in range(len(xsb_matrix)):
            cls.staticMatrix.append([])
            cls.movableMatrix.append([])
            for elem_idx in range(len(xsb_matrix[line_idx])):
                cls.staticMatrix[line_idx].append(None)
                cls.movableMatrix[line_idx].append(None)

        # Initialization of matrices from the Xsb matrix

        # legend:
        #   '#' = wall,  '$' = box, '.' = goal, '*' = box on goal, '@' = mover, '+' = mover on goal, '-' = floor, ' ' = floor
        y = 0
        for line_idx in range(len(xsb_matrix)):
            x = 0
            for elem_idx in range(len(xsb_matrix[line_idx])):
                e = xsb_matrix[line_idx][elem_idx]
                position = Position(x, y)
                if e == '#':
                    cls.staticMatrix[y][x] = Wall(canvas, position)
                elif e == '@':
                    cls.movableMatrix[y][x] = Mover(canvas, cls, position)
                    cls.staticMatrix[y][x] = Floor()
                    cls.mover = cls.movableMatrix[y][x]
                    cls.start_position = position
                    
                elif e == '$':
                    cls.movableMatrix[y][x] = Box(canvas, cls, position)
                    cls.staticMatrix[y][x] = Floor()
                elif e == '.':
                    cls.staticMatrix[y][x] = Goal(canvas, position)
                else:
                    cls.staticMatrix[y][x] = Floor()
                x = x + 1 
            y = y + 1
            x = 0
        cls.canvas.tag_raise("movable","static")
        return cls
 
    def at(self, position: Position) -> Entity:
        if self.movableMatrix[position.y][position.x] is not None:
            return self.movableMatrix[position.y][position.x]
            
        return self.staticMatrix[position.y][position.x]

    # def isPositionValid(self, position):

    def has_free_place_at(self, position):
        return self.at(position).is_free_place()
        
    
"""
Floor:
    Represents an empty cell in the matrix
    (no None in the matrix)
"""
class Floor(Entity):
    def __init__(self):
        pass
    def isMovable(self):
        return False
    def can_be_covered(self):
        return True
    def xsb_char(self):
        return ' '
    def is_free_place(self):
        return True
"""
Goal:
    Represents a location to be covered by a BOX (game objective).
    The mover must cover all these cells with boxes.
    A Goal is static, it is always drawn below:
        The zOrder is ensured by the tag of create_image (tag='static')
        and self.canvas.tag_raise("movable","static") in Level
"""
class Goal(Entity):
    def __init__(self, canvas, position):
        self.canvas: tk.Canvas = canvas
        self.position: Position = position
        self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/goal.png"))
        self.id = self.canvas.create_image(self.position.get_x() * IMAGE_SIZE, self.position.get_y() * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="static")


    def isMovable(self):
        return False

    def can_be_covered(self):
        return True
        
    def xsb_char(self):
        return '.'

    def is_free_place(self):
        return False

"""
Wall: to delimit the walls
    The mover cannot pass through a wall.
    A Wall is static, it is always drawn below:
        The zOrder is ensured by the tag of create_image (tag='static')
        and self.canvas.tag_raise("movable","static") in Level
"""
class Wall(Entity):
    def __init__(self, canvas, position):
        self.canvas: tk.Canvas = canvas
        self.position: Position = position
        self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/wall.png"))
        self.id = self.canvas.create_image(self.position.get_x() * IMAGE_SIZE, self.position.get_y() * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="static")

    def getHeight(self):
        return IMAGE_SIZE
    
    def getWidth(self):
        return IMAGE_SIZE

    def isMovable(self):
        return False

    def can_be_covered(self):
        return False

    def xsb_char(self):
        return '#'

    def is_free_place(self):
        return False

"""
Box: Box to be moved by the mover.
    Since a box needs to be moved, the canvas and the matrix are necessary to
    reconstruct the image and implement its movement (in the canvas and in the matrix)
    A Box is "movable", it is always drawn above the "static" objects:
        The zOrder is ensured by the tag of create_image (tag='movable')
        and self.canvas.tag_raise("movable","static") in Level
    A Box is represented differently (different image) depending on whether it is on a Goal or not.
 """
class Box(Entity):
    def __init__(self, canvas: tk.Canvas, wharehouse: WharehousePlan, position: Position, ongoal: bool = False):
        self.canvas: tk.Canvas = canvas
        self.wharehouse: WharehousePlan = wharehouse
        self.position: Position = position
        self.onGoal: bool = ongoal
        if self.onGoal:
            self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/boxOnTarget.png"))
            self.startOnGoalAnimation()
        else:
            self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/box.png"))
        self.id = self.canvas.create_image(self.position.get_x() * IMAGE_SIZE, self.position.get_y() * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")

    def isMovable(self):
        return True

    def can_be_covered(self):
        return False

    def move_towards(self, direction):
        self.wharehouse.movableMatrix[self.position.y][self.position.x] = None
        self.position = self.position.position_towards(direction, 1)
        self.wharehouse.movableMatrix[self.position.y][self.position.x] = self

    def xsb_char(self):
        if self.under.is_free_place(): return '$'
        else: return '*'

    def is_free_place(self):
        return False
    
    def __eq__(self, other):
        # Define here the comparison logic for Box objects
        # For example, if the attributes are equal, return True, otherwise False
        res = self.canvas == other.canvas and self.wharehouse == other.wharehouse and self.position.get_x() == other.position.get_x() and self.position.get_y() == other.position.get_y()
        return res
    
    def startOnGoalAnimation(self):
        self.OnGoalAnimation(3)     

    def clean_up_animation(self):
        self.canvas.delete("OnGoal")
        self.canvas.update()

    def OnGoalAnimation(self,count):
        if count > 0:
            self.canvas.create_oval(self.position.x * IMAGE_SIZE +64 - count*2, self.position.y * IMAGE_SIZE +64 -count*2, self.position.x * IMAGE_SIZE + count*2, self.position.y * IMAGE_SIZE+count*2, outline="yellow", width=4, tag="OnGoal")
            self.canvas.after(50, self.clean_up_animation)
            self.canvas.after(50, self.OnGoalAnimation, count-1)
        
        # call clean_up_animation after 1000ms
        self.canvas.after(100, self.clean_up_animation)

"""
Mover: This is the mover.
    The Mover class implements the game logic in #can_move and #move_towards.
    Since a Mover moves, the canvas and the matrix are necessary to
    reconstruct the image and implement its movement (in the canvas and in the matrix).
    A Mover is "movable", it is always drawn above the "static" objects:
        The zOrder is ensured by the tag of create_image (tag='movable')
        and self.canvas.tag_raise("movable","static") in Level.
    A Box is represented differently (different image) depending on the direction of movement (even if the movement turns out to be impossible).
"""
class Mover(object):
    def __init__(self, canvas, wharehouse, position):  
        self.canvas: tk.Canvas = canvas
        self.wharehouse: WharehousePlan = wharehouse
        self.position: Position = position
        self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/player.png"))
        self.id = self.canvas.create_image(self.position.get_x() * IMAGE_SIZE, self.position.get_y() * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")
        

    def is_moveable(self):
        return True

    """
        Returns True if the Mover can move in the requested direction.
        The calculation requires seeing the adjacent element but also the next element (offset of 2).
    """
    def can_move(self, direction: Direction):
        adjacent_position = self.position.position_towards(direction, 1)
        next_position = self.position.position_towards(direction,2)
        if self.wharehouse.at(self=self.wharehouse, position=adjacent_position).can_be_covered():
            return True
        elif self.wharehouse.at(self=self.wharehouse, position=adjacent_position).isMovable() and self.wharehouse.at(self=self.wharehouse, position=next_position).can_be_covered():
            self.push(direction)
            return True
        else :
            self.start_impossible_push_animation()
            return False

    """
        For the movement, it is necessary to possibly move the Box and then move the Mover.
    """
    def move_towards(self, direction):
        self.setup_image_for_direction(direction)
        if not self.can_move(direction):
            return
        self.canvas.delete(self.id)
        # calculation of the position of the adjacent element
        adjacent_position = self.position.position_towards(direction, 1)
        x = self.position.x
        y = self.position.y

        self.wharehouse.movableMatrix[adjacent_position.y][adjacent_position.x] = self.wharehouse.movableMatrix[y][x]
        self.wharehouse.movableMatrix[y][x] = None

        self.position.x = adjacent_position.x
        self.position.y = adjacent_position.y

         
        self.id = self.canvas.create_image(self.position.x * IMAGE_SIZE, self.position.y * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")
        self.canvas.update()

    """
        The Mover is represented differently depending on the direction of movement.
    """
    def setup_image_for_direction(self, direction: Direction):
        match direction:
            case Direction.Up:
                self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/playerUp.png"))
                self.id = self.canvas.create_image(self.position.x * IMAGE_SIZE, self.position.y * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")
            case Direction.Down:
                self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/player.png"))
                self.id = self.canvas.create_image(self.position.x * IMAGE_SIZE, self.position.y * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")
            case Direction.Left:
                self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/playerLeft.png"))
                self.id = self.canvas.create_image(self.position.x * IMAGE_SIZE, self.position.y * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")
            case Direction.Right:
                self.image = tk.PhotoImage(file=os.path.join(os.path.dirname(__file__), "assets/playerRight.png"))
                self.id = self.canvas.create_image(self.position.x * IMAGE_SIZE, self.position.y * IMAGE_SIZE, image=self.image, anchor=tk.NW, tag="movable")

    """
        For the movement:
            - image changed according to the direction
            - if we cannot move in this direction -> abandon
            - otherwise, the Mover is moved
    """
    def push(self, direction):
        position_new_box = self.position.position_towards(direction, 2)
        position_intermediate = self.position.position_towards(direction, 1)
        # check if the box is on a goal
        if self.wharehouse.staticMatrix[position_new_box.y][position_new_box.x].xsb_char() == '.':
            self.wharehouse.movableMatrix[position_intermediate.y][position_intermediate.x] = None
            self.wharehouse.movableMatrix[position_new_box.y][position_new_box.x] = Box(self.canvas, self.wharehouse, position_new_box, True)
            if(self.end_game()):
                username = tkinter.simpledialog.askstring("Sokoban", "You won!\n Enter your name:")
                Player.win(username, self.wharehouse.get_level_num(self.wharehouse))
        else:
            self.wharehouse.movableMatrix[position_new_box.y][position_new_box.x] = Box(self.canvas, self.wharehouse, position_new_box)
            self.wharehouse.movableMatrix[position_intermediate.y][position_intermediate.x] = None
        
        
        
        

    def end_game(self):
        for line in self.wharehouse.staticMatrix:
            for elem in line:
                if self.is_goal_not_covered(elem):
                    return False
        return True

    def is_goal_not_covered(self, elem):
        if elem is not None and elem.xsb_char() == '.':
            y = elem.position.y
            x = elem.position.x
            if self.is_box_not_on_goal(y, x):
                return True
        return False

    def is_box_not_on_goal(self, y, x):
        if self.wharehouse.movableMatrix[y][x] is not None:
            if self.wharehouse.movableMatrix[y][x] != Box(self.canvas, self.wharehouse, Position(x, y), True):
                return True
        else:
            return True
        return False

    def xsb_char(self):
        if self.under.is_free_place(): return '@'
        else: return '+'

    def is_free_place(self):
        return False

    def start_impossible_push_animation(self):
        self.impossible_push_animation(3)     

    def clean_up_animation(self):
        self.canvas.delete("impossiblePush")
        self.canvas.update()

    def impossible_push_animation(self,count):
        if count > 0:
            self.canvas.create_oval(self.position.x * IMAGE_SIZE +64 - count*2, self.position.y * IMAGE_SIZE +64 -count*2, self.position.x * IMAGE_SIZE + count*2, self.position.y * IMAGE_SIZE+count*2, outline="red", width=4, tag="impossiblePush")
            self.canvas.after(50, self.clean_up_animation)
            self.canvas.after(50, self.impossible_push_animation, count-1)
        
        # call clean_up_animation after 100ms
        self.canvas.after(100, self.clean_up_animation)
        
        
            

"""
    The game with everything needed to draw and store/manage the matrix of elements.
    
"""
class Level(object):
    def __init__(self, root, xsb_matrix, level_num):
        self.root = root

        # calculation of the matrix dimensions
        nbrows = len(xsb_matrix)
        nbcolumns = 0

        for line in xsb_matrix:
            nbc = len(line)
            if nbc > nbcolumns:
                nbcolumns = nbc

        self.canvas = tk.Canvas(self.root, width=IMAGE_SIZE * nbcolumns, height=IMAGE_SIZE * nbrows, bg="gray")

        self.wharehouse = WharehousePlan.from_xsb_matrix(xsb_matrix,self.canvas)
        self.wharehouse.level_num = level_num
        
        self.mover = self.wharehouse.get_mover(self.wharehouse)

        self.canvas.pack()
        self.root.bind("<Key>", self.keypressed)
        self.root.geometry(str(IMAGE_SIZE * nbcolumns) + "x" + str(IMAGE_SIZE * nbrows))

    def keypressed(self, event):
        direction = None
        if event.keysym == 'Up':
            direction = Direction.Up
        elif event.keysym == 'Down':
            direction = Direction.Down
        elif event.keysym == 'Left':
            direction = Direction.Left
        else:
            direction = Direction.Right

        self.mover.move_towards(direction)
         
class Sokoban(object):
    '''
    Main Level class
    '''
    
    def __init__(self):
        self.root = tk.Tk()
        #self.root.resizable(False, False)
        self.root.title("Sokoban")
        self.level = None
        self.level_num = 0
        self.table = tk.Frame(self.root)
        self.table.pack()
        self.table.grid(row=0, column=0)
        # allows to fix the window size
        self.root.geometry("500x300")
        # create the score.json file if it does not exist
        if not os.path.isfile(os.path.join(os.path.dirname(__file__), SCORE_FILE)):
            f = open(os.path.join(os.path.dirname(__file__), SCORE_FILE),'w')
            f.write('{}')
            f.close()
        
    def score(self):
        self.players = Players()
        Players.read_from_file()
        # Display players in a tkinter table
        self.players = Players.read_from_file()
        
        message = ""
        for i in range(len(self.players)):
            message += str(self.players[i].username) + " : " + str(self.players[i].score) + "\n"
        messagebox.showinfo("Player Scores", message)
        

    def start(self):
        if self.table is not None:
            self.table.destroy()
            self.table = None
        if self.level is not None:
            self.level.canvas.pack_forget()
        self.level = Level(self.root, sokobanXSBLevels.SokobanXSBLevels[self.level_num],self.level_num)
        self.level.canvas.pack(),    

    def choose_level(self):
        self.level_num = tk.simpledialog.askinteger("Level", "Choose a level (0-101)", minvalue=0, maxvalue=101)
        self.start()
    
    def menu(self):
        self.root.config(menu=tk.Menu(self.root))
        self.root.config(menu=tk.Menu(self.root))
        menu = tk.Menu(self.root)
        menu.add_command(label="Choose a level", command=self.choose_level)
        menu.add_command(label="Restart", command=self.start)
        menu.add_command(label="Scores", command=self.score)
        menu.add_command(label="Quit", command=self.root.destroy)
        self.root.config(menu=menu)

    def play(self):
        self.root.mainloop()


jeu = Sokoban()
jeu.menu()
jeu.play()