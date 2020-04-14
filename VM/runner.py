import argparse
from redis import Redis
import os
from itertools import permutations
from multiprocessing import Process


cli = Redis('localhost')

parser = argparse.ArgumentParser()
parser.add_argument("y3", nargs='?')
parser.add_argument("y9", nargs='?')
parser.add_argument("m", nargs='?')
parser.add_argument("o", nargs='?')
args = parser.parse_args()
fr = open("val/results.txt","w")
fv3 = open("val/v3.txt", "r")
fv9 = open("val/v9.txt", "r")
fo = open("val/oid.txt", "r")
fm = open("val/mrcnn.txt", "r")
cli.set(("score"), str(0.0))
cli.set(("total"), str(0))
cli.set("miss",str(0))
#count lines
images = sum(1 for line in fv3)
fv3 = open("val/v3.txt", "r")
def run():
    for i in range(1):
        perm   = ()
        done = []
        if i == 1:
            perm = permutations(["0","-1","-1","-1"])
        if i ==2:
            perm = permutations(["0","0","-1","-1"])
        if i ==3 :
            perm = permutations(["0","0","0","-1"])
        if i ==4:
            perm = permutations(["0","0","0","0"])
        perm = permutations(["0","0","0","0"])
        for p in list(perm):
            if not (p in done):
                print("CYCLE: " + str(list(p)))
                done.append(p)
                cli.set(("score"), str(0.0))
                cli.set(("total"), str(0))
                cli.set("miss",str(0))
                for i in range(len(os.listdir("val/data"))):
                    try:
                        y3arr = fv3.readline().split(".jpg")[1].strip().replace(",", " ").split("//")
                        y3arr = [x.strip() for x in y3arr]
                        del y3arr[-1]
                    except:
                        print("error: " + fv3.readline())

                    y9arr = fv9.readline().split(".jpg")[1].strip().replace(",", " ").split("//")
                    y9arr = [x.strip() for x in y9arr]
                    del y9arr[-1]

                    oidarr = fo.readline().split(".jpg")[1].strip().replace(",", " ").split("//")
                    oidarr = [x.strip() for x in oidarr]
                    del oidarr[-1]

                    marr = fm.readline().split(".jpg ")[1].split("  ")
                    del marr[-1]

                    cli.set('writev3', str(y3arr))
                    cli.set('write9000', str(y9arr))
                    cli.set('writeoid', str(oidarr))
                    cli.set('writemrcnn', str(marr))
                    cli.set('place', str(i))
                    #y3 y9 m o
                    s = "python3 exec-val.py"
                    fs = ""
                    for pe in p:
                        s =  s + " " + pe
                        fs = fs + "_" + pe
                    os.system(s)
                    #print(fs)
                    #print("\n//////////////////////////////////////\n")
                sout = fs + ": " + str(cli.get("score").decode())+ " "+str(cli.get("total").decode())  + "\n"
                fr.write(fs + ": " + str(cli.get("score").decode())+" " +  str(cli.get("total").decode())  + "\n")
                print("DONE: " + sout)
                fv3.seek(0)
                fv9.seek(0)
                fo.seek(0)
                fm.seek(0)
run()
