import json
import boto3
import logging
from botocore.exceptions import ClientError
import flask 
import os
import sys
import base64
client = boto3.client('textract')
def extractext(filestring):
	with open(filestring, "rb") as image:
		f = image.read() 
		b = bytearray(f)
		response = client.detect_document_text(
		Document={
			'Bytes': b
		}
		)
		columns = []
		lines = []
		for item in response["Blocks"]:
		      if item["BlockType"] == "LINE":
		        column_found=False
		        for index, column in enumerate(columns):
		            bbox_left = item["Geometry"]["BoundingBox"]["Left"]
		            bbox_right = item["Geometry"]["BoundingBox"]["Left"] + item["Geometry"]["BoundingBox"]["Width"]
		            bbox_centre = item["Geometry"]["BoundingBox"]["Left"] + item["Geometry"]["BoundingBox"]["Width"]/2
		            column_centre = column['left'] + column['right']/2

		            if (bbox_centre > column['left'] and bbox_centre < column['right']) or (column_centre > bbox_left and column_centre < bbox_right):
		                lines.append([index, item["Text"]])
		                column_found=True
		                break
		        if not column_found:
		            columns.append({'left':item["Geometry"]["BoundingBox"]["Left"], 'right':item["Geometry"]["BoundingBox"]["Left"] + item["Geometry"]["BoundingBox"]["Width"]})
		            lines.append([len(columns)-1, item["Text"]])

		lines.sort(key=lambda x: x[0])
		str = ""
		for line in lines:
			str = str+line[1]
			str = str + '\n'
		str = str.strip()
		print(str)
if(len(sys.argv[1:]) == 1):
	extractext(sys.argv[1])
else:
	print("Invalid file call")

