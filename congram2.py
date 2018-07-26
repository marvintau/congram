# -*- encoding: utf-8 -*-

import os
import sys
import itertools
import time

import numpy as np

def flatten(l):
    if l == []:
        return []
    elif not isinstance(l[0], list):
        return l
    else:
        return list(itertools.chain.from_iterable(l))

def group_by(lis, key):
    groups = itertools.groupby(sorted(lis, key=key), key)
    return [list(dat) for _, dat in groups]


color_func = {
    "BlueGreenYellow" : lambda (x):Color(
        int((0.14628343 - 0.61295736*x + 1.36894882*x*x)*127),
        int((0.01872288 + 1.65862067*x - 0.8011199 *x*x)*127),
        int((0.42712882 + 0.5047786 *x - 0.61649645*x*x)*127)
    ),
    "Sandy": lambda x:Color(
        int(( 0.60107395 + 1.63435499*x - 1.9800948 *x*x)*127),
        int(( 0.25372145 + 1.98482627*x - 1.93612357*x*x)*127),
        int(( 0.20537569 + 0.42332151*x - 0.47753999*x*x)*127)
    ),
    "Plum" : lambda x:Color(
        int((0.136180 + 0.775009*x + -0.133166*x*x)*127),
        int((0.036831 + 0.040629*x + 0.781372*x*x)*127),
        int((-0.087716 + 1.345565*x + -0.743961*x*x)*127)
    )
}

def full_color(color_scheme_name, val, minval, maxval):
    normed_val = (val-minval)/(maxval-minval)
    color = color_func[color_scheme_name](normed_val)
    return CharColor(color*2, color)


def ranged_color(color_func, val, minval, maxval):
    return color_func((val-minval)/(maxval-minval))

class Pos:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __add__(self, pos):
        return Pos(self.row + pos.row, self.col + pos.col)

    def __mul__(self, pos_time):
        if type(pos_time) is tuple:
            return Pos(self.row * pos_time[0], self.col * pos_time[1])
        else:
            return Pos(self.row * pos_time.row, self.col * pos_time.col)

    def __str__(self):
        return "{%d, %d}" % (self.row, self.col)

    def t(self):
        return Pos(self.col, self.row)

    def corners(self):
        return [Pos(0, 0),               Pos(self.row, 0),
                Pos(self.row, self.col), Pos(0, self.col)]

    def center(self):
        return Pos(int(round(self.row*0.5)), int(round(self.col*0.5)))

    # check if pos is on bottom-right side of self. Used for checking a rect is
    # enclosed by another.
    def deeper_than(self, pos):
        return self.row >= pos.row and self.col >= pos.col

    def shallower_than(self, pos):
        return self.row <= pos.row and self.col <= pos.col

class Color:
    def __init__(self, r, g, b):
        self.r = int(r)
        self.g = int(g)
        self.b = int(b)

    def __add__(self, inc):
        if type(inc) == inc and len(inc) == 3:
            return Color(self.r + inc[0], self.g + inc[1], self.b + inc[2])
        elif type(inc) == Color:
            return Color(self.r + inc.r, self.g + inc.g, self.b + inc.b)
        elif type(inc) == int:
            return Color(self.r + inc, self.g + inc, self.b + inc)
        else:
            raise TypeError("operand type must be either 3-tuple or Color")

    def __mul__(self, inc):
        if type(inc) == tuple and len(inc) == 3:
            return Color(self.r * inc[0], self.g * inc[1], self.b * inc[2])
        elif type(inc) == int:
            return Color(self.r * inc, self.g * inc, self.b * inc)
        else:
            raise TypeError("operand type must be either 3-tuple or int")

    def __str__(self):
        return "{%d, %d, %d}" % (self.r, self.g, self.b)


class CharColor:
    def __init__(self, fore=None, back=None):

        if fore is None:
            self.fore = Color(0, 0, 0)
        elif type(fore) == tuple and len(fore) == 3:
            self.fore = Color(*fore)
        else:
            self.fore = fore

        if back is None:
            self.back = Color(0, 0, 0)
        elif type(back) == tuple and len(back) == 3:
            self.back = Color(*back)
        else:
            self.back = back

    def __add__(self, inc):
        if type(inc) == tuple:
            if len(inc) == 2:
                return CharColor(self.fore + inc[0], self.back + inc[1])
            elif len(inc) == 3:
                return CharColor(self.fore + inc, self.back + inc)
            else:
                raise TypeError("operand type must be tuple")
        elif type(inc) is int:
            return CharColor(self.fore + inc, self.back + inc)
        else:
            raise TypeError("operand type must be tuple")

    def __mul__(self, inc):
        if type(inc) == tuple:
            if len(inc) == 2:
                return CharColor(self.fore * inc[0], self.back * inc[1])
            elif len(inc) == 3:
                return CharColor(self.fore * inc, self.back * inc)
            else:
                raise TypeError("operand type must be tuple")
        elif type(inc) is int:
            return CharColor(self.fore * inc, self.back * inc)
        else:
            raise TypeError("operand type must be tuple")

    def __str__(self):
        return str(self.fore) + " " + str(self.back)


class Stroke:
    def __init__(self, pos, text, color):
        self.pos = pos
        self.color = color
        self.text = text

    def trunc(self, num, is_from_left=True):

        # 当从左边trunc时，text删去开头的num个字符，同时pos向右推进num个字符
        # ；当从右边trunc时，只需要去掉text末尾的num个字符，不需要改起始位置

        if is_from_left:
            trunced = len(self.text) - num
            return Stroke(self.pos + Pos(0, trunced), self.text[trunced:], self.color)
        else:
            return Stroke(self.pos, self.text[:num], self.color)

    def shaded_by(self, next):

        # 讨论next（另一个Stroke）对自己遮挡的情况，先获取两个对象的左右
        # 边界。首先考虑互不遮挡的情况，即next右边界在self左边界的左边，或者next
        # 左边界在self右边界的右边。若不是这种情况，则当next左边界在self左边界右边

        self_l = self.pos.col
        self_r = self.pos.col + len(self.text)
        next_l = next.pos.col
        next_r = next.pos.col + len(next.text)

        l_shaded = next_l <= self_l
        r_shaded = next_r >= self_r
        dodged   = self.pos.row != next.pos.row or next_r < self_l or next_l > self_r

        if dodged: # dodged
            return [self]
        elif l_shaded and r_shaded:
            return []
        elif not (l_shaded or r_shaded):
            return [self.trunc(next_l - self_l, is_from_left=False),
                    self.trunc(self_r - next_r, is_from_left=True)]
        else:
            if l_shaded:
                return [self.trunc(self_r - next_r, is_from_left=True)]
            if r_shaded:
                return [self.trunc(next_l - self_l, is_from_left=False)]

    def __str__(self):

        COL_FORE = 38
        COL_BACK = 48

        COL_RESET = '\x01\x1b[0m\x02'
        COL_SEQ = '\x01\x1b[{z};2;{r};{g};{b}m\x02'

        c = self.color
        fore = COL_SEQ.format(z=COL_FORE, r=c.fore.r, g=c.fore.g, b=c.fore.b)
        back = COL_SEQ.format(z=COL_BACK, r=c.back.r, g=c.back.g, b=c.back.b)
        return fore + back + self.text + COL_RESET


class Rect:

    render_time = 0
    render_count = 0

    def __init__(self,
                 pos=Pos(0, 0),
                 size=Pos(10, 20),
                 text="text",
                 color=CharColor((127, 127, 127), (240, 240, 240))):

        self.pos   = pos
        self.size  = size
        self.text  = text
        self.color = color

        self.children = []

    def add_child(self, child):
        self_bottom_right = self.pos + self.size
        child_bottom_right = child.pos + child.size

        if child.pos.deeper_than(self.pos) and\
        child_bottom_right.shallower_than(self_bottom_right):
            self.children.append(child)

    def render(self, pos):

        strokes = []

        # 以下是当前Rect生成的Stroke.
        for line in range(self.size.row):
            if line == int(round(self.size.row*0.5)) - 1:
                stroke_text = self.text.center(self.size.col, " ")
            else:
                stroke_text = "".ljust(self.size.col, " ")
            stroke_pos = self.pos + pos + Pos(line, 0)
            strokes.append(Stroke(stroke_pos, stroke_text, self.color))

        for child in self.children:
            strokes.extend(child.render(self.pos + pos))

        return strokes

    def draw(self):

        strokes = self.render(Pos(0, 0))
        strokes = group_by(strokes, lambda rs:rs.pos.row)

        for line in strokes:
            curr_line = [line[0]]
            for next_stroke in line[1:]:
                curr_line = flatten([curr.shaded_by(next_stroke) for curr in curr_line])
                curr_line.append(next_stroke)

            for rs in sorted(curr_line, key=lambda rs:rs.pos.col):
                sys.stdout.write(str(rs))
            sys.stdout.write('\n')


class Canvas(Rect):

    def __init__(self):
        rows, cols = os.popen('stty size', 'r').read().split()
        size = Pos(int(rows), int(cols)-1)
        color = CharColor()

        Rect.__init__(self, Pos(0, 0), size, "", color)
        self.cursor = Pos(0, 0)



class Grid(Rect):

    def __init__(self,
                 pos=Pos(0, 0),
                 table=[[]],
                 grid_size=Pos(3, 3),
                 back_color = CharColor((255, 255, 255), (127, 127, 127))):

        max_cell_size = 0
        for line in table:
            for cell, _ in line:
                if max_cell_size < len(cell):
                    max_cell_size = len(cell)
        grid_width = max_cell_size + 2 if max_cell_size + 2 > grid_size.col else grid_size.col
        grid_size = Pos(grid_size.row, max_cell_size + 2)

        table_size = Pos(len(table), len(table[0])) * grid_size
        #print table_size

        Rect.__init__(self, Pos(0, 0), table_size, "", back_color)


        for row, line in enumerate(table):
            for col, (cell, color) in enumerate(line):
                cell_pos = grid_size * Pos(row, col)
                self.add_child(Rect(cell_pos, grid_size, cell, color))

class Heatmap(Grid):

    def __init__(self,
                 pos=Pos(0, 0),
                 table=[[]],
                 grid_size=Pos(3, 3),
                 color_scheme="Plum",
                 back_color = CharColor()):

        minval = min([min(l) for l in table])
        maxval = max([max(l) for l in table])

        def table_item(cell, min_val, max_val, color_scheme):
            return ("%1.2f" % c, full_color(color_scheme, c, minval, maxval))

        table = [[ table_item(c, minval, maxval, color_scheme) for c in line] for line in table]
        Grid.__init__(self, Pos(0, 0), table, grid_size)


class Frame(Rect):

    corner_styles = {
        'rect' : ()
    }

    def __init__(self,
                 pos=Pos(0, 0),
                 rect=Rect(),
                 frame_sides = ('left', 'right', 'top', 'bottom'),
                 tick_rep = Pos(1, 1),
                 tick_off = Pos(1, 1),
                 corner_style = 'rect'
                 ):
        pass

if __name__ == "__main__":

    grid = np.random.random_sample(((12, 14)))

    canvas = Canvas()
    heat_map = Heatmap(table=grid.tolist())
    rect     = Rect(Pos(0, 0), Pos(40, 90))
    rect.add_child(heat_map)
    canvas.add_child(rect)
    canvas.draw()
