import json
import boto3
import logging
from botocore.exceptions import ClientError
import flask 
import os
import sys
import base64
client = boto3.client('textract')
with open('stopsign', "rb") as image:
    f = image.read()
    b = bytearray(f)
    response = client.detect_document_text(
    Document={
        'Bytes': b
    }
)
