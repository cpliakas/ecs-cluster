ECS_CLUSTER_S3_BUCKET := example

build: events.py
	pip install boto3 -t .
	rm -f events.zip && zip -x Makefile -x setup.cfg -r events.zip .

install:
	aws s3 cp events.zip s3://$(ECS_CLUSTER_S3_BUCKET)/lambda/events.zip

clean:
	ls | egrep -v '^(events.(py|zip)|Makefile|setup.cfg)$$' | xargs rm -rf
