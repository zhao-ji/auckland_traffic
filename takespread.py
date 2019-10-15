from math import ceil

def takespread(sequence, num):
    length = float(len(sequence))
    for i in range(num):
        yield sequence[int(length - 1 - ceil(i * length / num))]

if __name__ == "__main__":
    a = [1,2,3,4,5,6,7,8,9,10,11,12]
    b = 3
    print list(takespread(a, b))
