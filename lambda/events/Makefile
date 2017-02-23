ECS_CLUSTER_S3_BUCKET := example
ECS_CLUSTER_S3_KEY := lambda/handler.zip

build: handler.py
	pip install boto3 -t .
	rm -f handler.zip && zip -r handler.zip .

install:
	aws s3 cp handler.zip s3://$(ECS_CLUSTER_S3_BUCKET)/$(ECS_CLUSTER_S3_KEY)

clean:
	ls | egrep -v '^(handler.(py|zip)|Makefile|setup.cfg)$$' | xargs rm -rf
