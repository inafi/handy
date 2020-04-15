# Handy

The Handy as a visual aid for the blind. The Handy is a glove equipped with a raspberry pi that takes a picture of the user’s surroundings. It then uses several CV models to identify and locate the objects or text in the image. With this device, the visually impaired will have a device that describes their surroundings, helps them locate specific objects in real-time, and keep track of their possessions. See the video: https://youtu.be/_9c493aPXFI

## Setup

Aside from the AWS Services, below are the other components used in making the Handy

Android phone with google play services
Android Studios
Raspberry pi Zero W
ArduCam 175 Degree Viewfield Lens
LSM9DS1
4  Coin Vibration motors
4 LEDs
Push button for the rpi
(optional) portable power bank 

## Wiring the Raspberry Pi Zero W

![alt text](https://github.com/inafi/handy/blob/master/rpi/wiring.png)

## Installation

On both your local machine and  raspberry pi, run:
git clone https://github.com/inafi/handy.git

1. Downloading the App

On your machine, move ‘g’ into your Android studio projects folder
```
cp app/g ~/AndroidStudioProjects
```
Then launch

2. Setting up the Raspberry pi

On your raspberry pi: 

```
cd rpi
pip install -r requirements.txt
```

3. On the Ec2 instance
Running Program

On the Raspberry pi:

```
cd rpi
python3 run.py
```

On SageMaker

Configure your AWS credentials and install the necessary libraries through requirements.txt
Follow the steps given by the AWS Marketplace guide to configure the model in the AWS CLI environment

Then, on the Ec2 instance

```
cd VM
python3 runall.py
```

## Using the Glove and App

After running the commands above, wear the glove. To take a picture, press the button on the side of the glove with the camera facing the scene you want to analyze. From there, press the push button on the side of the glove and wait for the audio prompt. From there, choose a mode:

###### The Scan
This feature simply relays what the user’s surroundings are, along with the count of each object. For example, “1 table, 1 laptop, and 3 cups detected.” Say "scan" to activate this mode.

###### The Text
This feature reads out any text in the picture. It first says the surface the text was detected, such as a sign or a book, then the actual writing. For example, “The sign says, “No parking”. Say "text" to activate this mode.

###### The Search
This feature guides users towards the desired objects which they choose through audio input. Each detected object is accompanied by an x and y degree separation in relation to where the picture was taken. As soon as the picture is taken, the IMU built into the sleeve begins to track the user’s movement. This way, it calculates how far left, right, up or down the user has to move to be aligned with the desired object. To guide the user, vibration motors on the top, bottom, and both sides of the wrist vibrate to signal the user where to move. As the user gets closer to the object, the vibrations intensify until the use presses the button again to signal that they have located the object. Of course, moving in with the motors might be dangerous in some environments, as the user may collide with obstacles. To prevent this, an infrared sensor below the camera alerts the user when they are within 1.5 ft of an object with the audio producing, “collision alert” and then “safe distance” once the user has backed away. Say "search" and the name of the item you are looking for to activate this mode.

###### The Last Seen
This function asks the user for an object and then returns the time, place, and location the object was last seen. The detected objects for every picture are stored in the database, along with the time taken and the location of the phone. Using a search algorithm, the app is able to detect the latest log containing their object. Say "find" and the name of the item you are looking for to activate this mode.
