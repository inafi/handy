from redis import Redis
import time

cli = Redis("localhost")
cli.set("statex", 0)
cli.set("statez", 0)
while(True):
    print(cli.get("anglex") + " " + cli.get("anglez") + " " + cli.get("statex") + " " + cli.get("statez") + " " + cli.get("action") + " " + cli.get("count"))
