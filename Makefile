.PHONY: clean
clean:
	rm -rf __pycache__
	rm -rf img
	rm -f lambda.zip

.PHONY: zip
zip: clean
	zip -r lambda.zip *.py config.json json_data/* packages/* IPAexfont00401/* 

.PHONY: deploy
deploy:
	aws lambda update-function-code --region us-east-1 --function-name ${ENV}-mdt-${pkg} --zip-file fileb://bin/${pkg}/${ZIP}
