ECS_CLUSTER_S3_BUCKET := example

build: proxy.js
	rm -f proxy.zip && zip -x Makefile -r proxy.zip .

install:
	aws s3 cp proxy.zip s3://$(ECS_CLUSTER_S3_BUCKET)/lambda/proxy.zip
