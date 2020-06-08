import os
import time
t = time.time()
os.system("raspistill -vf -hf -o zoid.jpg -w 3280 -h 2464 -t 500")
print('pic taken', time.time() - t)
os.system("cp zoid.jpg ../")
os.chdir("../")
os.system("./du.sh upload zoid.jpg /")
