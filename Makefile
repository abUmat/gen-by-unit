.PHONY: clean
clean:
	rm -rf deployment_package
	rm -rf img

.PHONY: cp
cp:
	mkdir -p deployment_package
	cp -r src/* deployment_package/
	cp -r packages deployment_package/packages/
	cp -r IPAexfont00401 deployment_package/IPAexfont00401/
	cp -r json_data deployment_package/json_data/
	cp config.json deployment_package/

.PHONY: run
run: clean cp
	python3 deployment_package/main.py
	make clean

.PHONY: zip
zip: clean cp
	cd deployment_package && zip -r ../lambda.zip .
	make clean

.PHONY: deploy
deploy:
	aws lambda update-function-code --region us-east-1 --function-name prd-hobby-gen_by_unit --zip-file fileb://lambda.zip
