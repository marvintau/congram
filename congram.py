# -*- encoding: utf-8 -*-

import os
import sys
import time
import itertools
import numpy as np

def flatten(l):
    return list(itertools.chain.from_iterable(l))

def group_by(lis, key):
    groups = itertools.groupby(sorted(lis, key=key), key)
    return [list(dat) for _, dat in groups]

def get_term_size():
    rows, columns = os.popen('stty size', 'r').read().split()
    return int(rows), int(columns)

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

def size(l):
    return Pos(len(l), len(l[0]))


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
        elif type(inc) is int:
            return CharColor(self.fore * inc, self.back * inc)
        else:
            raise TypeError("operand type must be tuple")

    def __str__(self):
        return str(self.fore) + " " + str(self.back)

class Rect:
    """
    一个Rect对象包含了绘制屏幕上一块着色区域的信息，以及包含在这个区域内的所有
    子元素的信息。
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

        color = color * (2,1)
        self.add_empty_line(anchor)
        self.elems.append(Rect(anchor, color, text))

        self.current_line += 2

    def add_empty_line(self, pos):
        self.elems.append(Rect(Pos(pos.row, 0), CharColor(), " "*self.cols))


    def add_frame(self, size, anchor,
                  sides=("left", "right", "top", "bottom"),
                  frame_margin = Pos(3, 5),
                  x_tick_range=None,
                  y_tick_range=None,
                  rep=None,
                  x_off=None,
                  y_off=None):
        color = CharColor((255, 255, 255))

        # 四面边框和中间内容距离之和，比如如果左边距为1，上边距为2，则以下边距
        # 应该为(1*2+1, 2*2+1) = (3, 5)，考虑到等宽字体的宽高比例，这个比例是刚
        # 刚好的.

        size = size + frame_margin
        for l in range(size.row+1):
            self.add_empty_line(Pos(l, 0) + anchor)
            tick_char =  u"│"
            if x_off is not None and rep.col is not None:
                if (l + x_off) % rep.col == 0:
                    tick_char = u"├"
            if "left" in sides:
                self.elems.append(Rect(Pos(l, 0)+anchor, color, tick_char))
            if "right" in sides:
                self.elems.append(Rect(Pos(l, size.col)+anchor, color, u"│"))

        for l in range(1,size.col):
            tick_char =  u"─"
            if y_off is not None and rep.row is not None:
                if (l + y_off) % rep.row == 0:
                    tick_char = u"┴"
            if "top" in sides:
                self.elems.append(Rect(Pos(0, l)+anchor, color, u"─"))
            if "bottom" in sides:
                self.elems.append(Rect(Pos(size.row, l)+anchor, color, tick_char))

        for corner, char in zip(size.corners(), [u"┌", u"└", u"┘", u"┐"]):
            self.elems.append(Rect(anchor+corner, color, char))

    def add_cell(self, cell, size, color, anchor):

        """
        添加一个单元（可用于heatmap或其他表格）
        cell:   单元格内容
        size:   单元格长宽
        color:  单元格颜色
        anchor: 锚点
        """
        cell = cell.rjust(size.col)

        # 在若干行连续画长度为size.col的小色块，在中间那行写字
        for l in range(size.row):
            string = cell if l == size.row//2 else "".rjust(len(cell))
            self.elems.append(Rect(anchor + Pos(l, 0), color, string))

        return size

    def add_grid(self, table, cell_size, color_func, anchor=None):

        for [row_num, row] in enumerate(table):
            for [col_num, (cell, color)] in enumerate(row):
                pos = anchor + Pos(row_num, col_num) * cell_size
                self.add_cell(cell, cell_size, color, pos)

        return cell_size * Pos(row_num, col_num)

    def add_heatmap(self, table, color_func,
                    thermo=False,
                    draw_frame=False,
                    anchor=None):

        table_size = size(table)
        flat       = flatten(table)
        min_cell   = min(flat)
        max_cell   = max(flat)


        # 生成一个新的带颜色的表格，顺便获得最长单元格字符串的长度,
        # generate colored table along with the max length of string
        colored_table = []
        cell_len      = 0

        for lis in table:
            colored_table.append([])

            for cell in lis:
                cell_str   = " %1.2f " % cell
                cell_bc    = ranged_color(color_func, cell, min_cell, max_cell)
                cell_color = CharColor(cell_bc+127, cell_bc)
                colored_table[-1].append((cell_str, cell_color))

                if cell_len < len(cell_str):
                    cell_len = len(cell_str)
        cell_size  = Pos(3, cell_len)


        frame_margin = Pos(3, 5)

        # 如果没有指定锚点则默认对齐到画布中间
        # if anchor is not specified, then align to the center of canvas
        if anchor is None:
            frame_offset = frame_margin.center().col
            actual_left = (self.cols - len(table[0]) * cell_len) / 2
            anchor = Pos(self.current_line, actual_left)


        # 画边框，并决定单元格的起始位置
        # Draw the frame, and also decide where cells starts
        # if draw_frame is True:
        frame_size = self.add_frame(table_size * cell_size, anchor,
                    frame_margin=frame_margin,
                    rep=cell_size.t(), x_off=0, y_off=0)
        cell_anchor = anchor + frame_margin.center()
        # 画单元格
        # draw each cell
        self.add_grid(colored_table, cell_size, color_func, cell_anchor)

        return frame_size

        # Add a thermometer on the right side
#        thermo_left = len(table[0]) * cell_size.col + 10
#        for line in range(1, len(table) * 3 + 6):
#            pos = Pos(line, thermo_left) + anchor
#            back = color_func(1.0 - 1.0 * line / (len(table) * 3+3))
#            color = CharColor(Color(0, 0, 0), back)
#            self.elems.append(Rect(pos, color, "    "))
#
#        self.current_line += len(table)*3 + 4

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

    def render_line(self, elems_inline, is_reset=False):
        """
        render elements in single line
        """

        # Find all elements to be rendered in current line
        # elems_inline = [elem for elem in self.elems if elem.pos.row == line_num]

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
            visible_parts = flatten(visible_parts)

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

        render_lines = group_by(self.elems, lambda elem: elem.pos.row)

        for line_elems in render_lines:
            self.render_line(line_elems, is_reset)

    def stroke(self, text, c):

        COLOR_FORE = 38
        COLOR_BACK = 48

        color_seq = '\x01\x1b[{z};2;{r};{g};{b}m\x02'
        fore = color_seq.format(z=COLOR_FORE, r=c.fore.r, g=c.fore.g, b=c.fore.b)
        back = color_seq.format(z=COLOR_BACK, r=c.back.r, g=c.back.g, b=c.back.b)
        return fore+back+text


if __name__ == "__main__":
    curr_time = time.time()
    c = Canvas()
    grid = np.random.random_sample(((7, 10)))
    hist = np.random.random_sample(((15, 1)))
    c.add_text("This is a heatmap example", CharColor(color_func["Plum"](0.9)))
    c.add_heatmap(grid.tolist(), color_func["Plum"])
    # c.add_text("This is a histogram example", CharColor(color_func["BlueGreenYellow"](0.9)))
    print time.time() - curr_time
    #c.add_hist(grid.tolist(), color_func["BlueGreenYellow"])
    c.render(True)
