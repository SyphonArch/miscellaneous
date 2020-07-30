"""Comments were added a year after the coding, in an attempt to make sense of the logic."""
from itertools import permutations


def valid(x):  # x is a permutation
    for i in x:
        prerequisites = []
        if i % 2 == 0:  # prerequisites will contain adjacent odd numbers
            prerequisites.append(i - 1)
            prerequisites.append(i + 1)
        for p in prerequisites:
            if p in x:  # adjacent odd numbers within range
                if x.index(p) > x.index(i):  # even numbers should come after adjacent odd numbers
                    return False
    return True

for i in range(1, 10):
    a = permutations(range(1, i + 1))
    cnt = 0
    for x in a:
        if valid(x):
            cnt += 1
    print(i, cnt)


