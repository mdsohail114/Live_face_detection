from turtle import *
from colorsys import *
speed(0)
bgcolor("black")
h = 0
for i in range(90):
    color(hsv_to_rgb(h, 1, 1))
    h += 0.014
    left(1)
    forward(1)
    for j in range(5):
        left(5)
        circle(200)
    hideturtle()
done()    