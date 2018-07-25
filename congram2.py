# -*- encoding: utf-8 -*-

import sys
import itertools

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
        else:
            left  = () if l_shaded else self.trunc(next_l - self_l, is_from_left=False)
            right = () if r_shaded else self.trunc(self_r - next_r, is_from_left=True)
            return [left, right]

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

    def __init__(self, pos, size, text, color):

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
            strokes.append([Stroke(stroke_pos, stroke_text, self.color)])

        # 以下是Rect的子元素的Stroke，由于子元素之间也存在遮挡问题，因此在
        # 一次迭代内解决。由于子元素遮挡顺序由添加至children的顺序体现因此
        # 这个顺序相当于先处理Rect所有子元素中先插入的（也就是压在下面的）
        # 元素的遮挡情况.

        for child in self.children:
            child_strokes = child.render(self.pos + pos)

            for idx, line in enumerate(range(self.pos.row, self.size.row + self.pos.row)):

                # 当前行起始时只有Rect自己的stroke
                # 将每个子元素中同一行的stroke比较一下，最后加入子元素当前行
                # stroke要加一层list是为了之后的flatten操作
                for child_stroke in child_strokes:
                    if child_stroke.pos.row == line:
                        strokes[idx] = [s.shaded_by(child_stroke) for s in strokes[idx]]
                        strokes[idx].append([child_stroke])

                    # 将flatten过的strokes_line塞回strokes对应的行中
                    strokes[idx] = [s for s in flatten(strokes[idx]) if s != ()]

        # 执行完以上循环的strokes是一个list， 里面每个元素是处理完每一个子
        # 元素的遮挡后的strokes。它需要再flatten一次才能成为一维表返回上一
        # 级调用

        return flatten(strokes)

    def draw(self):

        # 绘制这个Rect，先获取它的strokes，按行数group_by
        strokes = self.render(Pos(0, 0))
        strokes = group_by(strokes, lambda rs:rs.pos.row)

        for line in strokes:
            for rs in sorted(line, key=lambda rs:rs.pos.col):
                sys.stdout.write(str(rs))
                #sys.stdout.write("(%d, %d)" % (rs.pos.col, rs.pos.col + len(rs.text)))
            sys.stdout.write('\n')


#rs1 = Stroke(Pos(1, 5), "123456789", CharColor((255,255,254), (127,127,127)))
#rs2 = Stroke(Pos(1, 6), "  ", CharColor((255,255,254)))
#lis = rs1.shaded_by(rs2)
#lis.append(rs2)
#lis.sort(key=lambda e:e.pos.col)
#for l in lis:
#    sys.stdout.write(str(l))

rect1 = Rect(Pos(0,0), Pos(20, 30), "aaaaaa", CharColor((0,0,0), (127, 127, 127)))
rect2 = Rect(Pos(1,1), Pos(18, 28), "aaaaaa", CharColor((0,0,0), (200, 200, 200)))
rect3 = Rect(Pos(1,1), Pos(16, 26), "aaaaaa", CharColor((0,0,0), (255, 255, 255)))

rect2.add_child(rect3)
rect1.add_child(rect2)
rect1.draw()
