import json
import boto3
import logging
from botocore.exceptions import ClientError
import flask 
import os
import sys
client = boto3.client('sagemaker')
client2 = boto3.client('sagemaker-runtime')
import base64
import json
def createndpointconfig():
    print(client.create_endpoint_config(
    EndpointConfigName='sample-endpointcfg-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2',
    ProductionVariants=[
        {
            'VariantName': 'variant-1',
            'ModelName': 'sample-model-D9949C88-FE3B-4A2D-923E-9458FE7E9F2C-1',
            'InitialInstanceCount': 1,
            'InstanceType': 'ml.m4.xlarge',
        },
    ]))

    print(client.create_endpoint(
    EndpointName='sample-endpoint-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2',
    EndpointConfigName='sample-endpointcfg-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2',
    ))
    create = False
    while(create is False):
        try:
            response = client.describe_endpoint(
        EndpointName='sample-endpoint-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2'
            )
        except:
            pass
        print(response["EndpointStatus"])
        if(response["EndpointStatus"] == "InService"):
            create = True
    print("endpoint created")
def describendpoint():
    response = client.describe_endpoint(
    EndpointName='sample-endpoint-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2'
            )
    
    if(response["EndpointStatus"] == "InService"):
        print("endpoint created")
    else:
        print(response["EndpointStatus"])
def deleteendpoint():
    print(client.delete_endpoint(
    EndpointName='sample-endpoint-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2'
    ))
def runprediction(files,ftype):
    with open(files, "rb") as image:
        f = image.read()
        b = bytearray(f)
        jsonstring = (client2.invoke_endpoint(
        EndpointName='sample-endpoint-134EEA74-A9CA-4B4F-8DB1-B9721EEFC63B-2',\
        Body=b,\
        ContentType=ftype,
        ))['Body'].read().decode("utf-8")
        jsonstring = json.loads(jsonstring)
        listofargs = []
        for i in jsonstring:
            secondlist = []
            secondlist.append(i["id"])
            secondlist.append(i["score"])
            secondlist.append([i["top"],i["left"],(int(i["right"])-int(i["left"])),(int(i["bottom"])-int(i["top"]))])
            listofargs.append(secondlist)
        print(listofargs) 
if(len(sys.argv[1:])>1):
    runprediction(sys.argv[1],sys.argv[2])
elif(len(sys.argv[1:]) == 1):
    deleteendpoint()
else:
    createndpointconfig()
