
build: handler.py
	pip install boto3 -t .
	rm -f handler.zip && zip -r handler.zip .

clean:
	ls | egrep -v '^(handler.(py|zip)|Makefile|setup.cfg)$$' | xargs rm -rf
