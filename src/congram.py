# -*- coding: utf-8 -*-

import os
import sys
import itertools
import numpy as np

from color_schemes import color_func


def get_term_size():
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)


class Pos:
    def __init__(self, row, col):
        self.row = row
        self.col = col

    def __add__(self, pos):
        return Pos(self.row + pos.row, self.col + pos.col)

    def __mul__(self, pos_time):
        if type(pos_time) is tuple:
            return Pos(self.row * pos_time[0], self.col * pos_time[1])
        return Pos(self.row * pos_time.row, self.col * pos_time.row)

    def __str__(self):
        return "{%d, %d}" % (self.row, self.col)

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
        elif type(inc) == float:
            return Color(int(self.r * inc), int(self.g * inc), int(self.b * inc))
        else:
            raise TypeError("operand type must be either 3-tuple or int")

    def __str__(self):
        return "{%d, %d, %d}" % (self.r, self.g, self.b)

class CharColor:
    def __init__(self, fore, back=None):

        if type(fore) == tuple and len(fore) == 3:
            self.fore = Color(*fore)
        else:
            self.fore = fore

        if back == None :
            self.back = Color(0,0,0)
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
                raise TypeError("operand type must be either 3-tuple or 2-tuple")
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
                raise TypeError("operand type must be either 3-tuple or 2-tuple")
        elif type(inc) is float:
            return CharColor(self.fore * inc, self.back * inc)
        else:
            raise TypeError("operand type must be tuple")

    def __str__(self):
        return str(self.fore) + " " + str(self.back)

class Rect:
    """
    Rect: Draw a rectangle area with given fore/back color and text content
          records position, size, color and content only.
    """

    def __init__(self, pos, color, text):

        self.pos   = pos
        self.color = color
        self.text  = text


class Canvas:


    rows, cols = get_term_size()

    # graphic elements hold by Canvas.
    elems = []

    # for successively adding elements
    current_line = 0

    def add_text(self, text, color, anchor=None):

        if anchor is None:
            anchor = Pos(self.current_line, (self.cols - len(text)) / 2)

        color = color * (0.5, 1.)
        self.add_empty_line(anchor)
        self.elems.append(Rect(anchor, color, text))

        self.current_line += 2

    def add_empty_line(self, pos):
        self.elems.append(Rect(Pos(pos.row, 0), CharColor((0,0,0)), " "*self.cols))


    def add_frame(self, size, anchor,
                  sides=("left", "right", "top", "bottom"),
                  x_tick_range=None,
                  y_tick_range=None,
                  x_rep=None,
                  y_rep=None,
                  x_off=None,
                  y_off=None):
        color = CharColor((255, 255, 255))

        for l in range(size.row+1):
            self.add_empty_line(Pos(l, 0) + anchor)
            tick_char =  u"│"
            if x_off is not None and x_rep is not None:
                if (l + x_off) % x_rep == 0:
                    tick_char = u"├"
            if "left" in sides:
                self.elems.append(Rect(Pos(l, 0)+anchor, color, tick_char))
            if "right" in sides:
                self.elems.append(Rect(Pos(l, size.col)+anchor, color, u"│"))

        for l in range(1,size.col):
            tick_char =  u"─"
            if y_off is not None and y_rep is not None:
                if (l + y_off) % y_rep == 0:
                    tick_char = u"┴"
            if "top" in sides:
                self.elems.append(Rect(Pos(0, l)+anchor, color, u"─"))
            if "bottom" in sides:
                self.elems.append(Rect(Pos(size.row, l)+anchor, color, tick_char))

        self.elems.append(Rect(anchor, color, u"┌"))
        self.elems.append(Rect(anchor+Pos(size.row, 0), color, u"└"))
        self.elems.append(Rect(anchor+Pos(size.row, size.col), color, u"┘"))
        self.elems.append(Rect(anchor+Pos(0, size.col), color, u"┐"))

    def add_grid(self, table, color_func, anchor=None):

        cell_size = 0

        min_cell = min([min(c) for c in table])
        max_cell = max([max(c) for c in table])

        # Get reformed string and calculate max length
        for row in table:
            for cell in row:
                try:
                    new_cell = "%1.2f" % cell
                except TypeError:
                    new_cell = cell

                if cell_size < len(new_cell):
                    cell_size = len(new_cell)
        cell_size += 2


        if anchor is None:
            anchor = Pos(self.current_line, (self.cols - len(table[0]) * cell_size - 7) / 3)

        self.add_frame(Pos(len(table)*3+3, len(table[0])*cell_size+5), anchor,
                       x_rep=3, x_off=0, y_rep=cell_size, y_off=0)

        def add_cell(cell, anchor, pos, isBlank=False):

            pos   = pos * (1, cell_size) + anchor + Pos(0, 2)
            back  = color_func((cell-min_cell)/(max_cell-min_cell))
            color = CharColor(back, back) * (1., 0.5)

            cell = "" if isBlank else "%1.2f" % cell if type(cell) is float else cell
            cell = cell.rjust(cell_size - 2)

            self.elems.append(Rect(pos, color, " " + cell + " "))


        # Add each cell into element table
        # and calculates the max cell length
        cell_anchor = anchor + Pos(2, 1)
        for [row_num, row] in enumerate(table):
            for [col_num, cell] in enumerate(row):
                add_cell(cell, cell_anchor, Pos(row_num*3+0, col_num), True)
                add_cell(cell, cell_anchor, Pos(row_num*3+1, col_num))
                add_cell(cell, cell_anchor, Pos(row_num*3+2, col_num), True)

        # Add a thermometer on the right side
        thermo_left = len(table[0]) * cell_size + 10
        for line in range(1, len(table) * 3 + 6):
            pos = Pos(line, thermo_left) + anchor
            back = color_func(1.0 - 1.0 * line / (len(table) * 3+3))
            color = CharColor(Color(0, 0, 0), back)
            self.elems.append(Rect(pos, color, "    "))

        self.current_line += len(table)*3 + 4

    def add_hist(self, hist, color_func, anchor=None):

        max_val = max(hist[0])
        height  = 30
        bar_width = 5
        if anchor is None:
            anchor = Pos(self.current_line, (self.cols - len(hist[0]) * bar_width) / 2)

        self.add_frame(Pos(height + 3, len(hist[0])*bar_width + 5), anchor,
                       x_rep=3, x_off=0, y_rep=bar_width, y_off=0)

        hist_anchor = anchor + Pos(2, 3)
        for line in range(height):
            for ith, val in enumerate(hist[0]):
                pos  = Pos(line, ith*bar_width) + hist_anchor
                if height * (1 - val/max_val) < line:
                    color = color_func(val/max_val)
                    self.elems.append(Rect(pos, CharColor(color, color*2), "    "))

        self.current_line += 30

    def render_line(self, line_num, is_reset=False):
        """
        render elements in single line
        """

        # Find all elements to be rendered in current line
        elems_inline = [elem for elem in self.elems if elem.pos.row == line_num]

        visible_parts = []

        def visible_check((A_left, A_right, _), (B_left, B_right, B_id)):

            # compare the left/right bound of new element with each
            # existing bound.

            A_left_shaded  = A_left  <= B_left
            A_right_shaded = A_right >= B_right
            A_left_dodged  = A_right <  B_left
            A_right_dodged = A_left  >  B_right

            # Four cases of shading:
            # 1. dodged: the fore and back element doesn't overlap
            # 2. shaded: fore element shaded at left or right bound of back
            #            element.
            # 3. split:  fore element splits back element into two visible
            #            parts.

            if A_left_dodged or A_right_dodged: # dodged
                return ((B_left, B_right, B_id),)
            elif not (A_left_shaded or A_right_shaded): # splitted
                return ((B_left,  A_left,  B_id),(A_right, B_right, B_id))
            elif (A_left_shaded and A_right_shaded): # fully shaded
                return []
            else: # partially shaded
                if A_left_shaded:
                    return ((A_right, B_right, B_id),)
                if A_right_shaded:
                    return ((B_left, A_left, B_id),)

        for elem_i, elem in enumerate(elems_inline):

            elem_bound = (elem.pos.col, elem.pos.col + len(elem.text), elem_i)

            for i, part in enumerate(visible_parts):
                visible_parts[i] = visible_check(elem_bound, part)
            visible_parts.append((elem_bound,))

            # list flatten operation by itertools.chain flatten both list and
            # tuple (and all iterables), thus we have to coat it with one more
            # tuple in order to maintain the form.
            visible_parts = list(itertools.chain.from_iterable(visible_parts))

        visible_parts = sorted(visible_parts, key=lambda x:x[0])

        # handles if no elements in this line
        strokes = "" if visible_parts == [] else " " * visible_parts[0][0]

        COLOR_RESET = '\x01\x1b[0m\x02'

        for part in visible_parts:
            elem = elems_inline[part[2]]
            color = elem.color
            text = elem.text[part[0] - elem.pos.col : part[1] - elem.pos.col]
            strokes += self.stroke(text, color)
            strokes += COLOR_RESET if is_reset else ""

        sys.stdout.write(strokes + COLOR_RESET)
        sys.stdout.write("\n")

    def render(self, is_reset=False):
        sys.stdout.flush()
        sys.stdout.write("\n")
        for line in range(self.rows):
            self.render_line(line, is_reset)

    def stroke(self, text, c):

        COLOR_FORE = 38
        COLOR_BACK = 48

        color_seq = '\x01\x1b[{z};2;{r};{g};{b}m\x02'
        fore = color_seq.format(z=COLOR_FORE, r=c.fore.r, g=c.fore.g, b=c.fore.b)
        back = color_seq.format(z=COLOR_BACK, r=c.back.r, g=c.back.g, b=c.back.b)
        return fore+back+text


if __name__ == "__main__":
    c = Canvas()
    grid = np.random.random_sample(((7, 10)))
    hist = np.random.random_sample(((15, 1)))
    c.add_text("This is a heatmap example", CharColor(color_func["Plum"](0.9)))
    c.add_grid(grid.tolist(), color_func["Plum"])
    c.add_text("This is a histogram example", CharColor(color_func["BlueGreenYellow"](0.9)))
    #c.add_hist(grid.tolist(), color_func["BlueGreenYellow"])
    c.render(True)
