DEPLOY_PACKAGE=deployment_package

.PHONY: clean
clean:
	rm -rf ${DEPLOY_PACKAGE}
	find . -type d -name "__pycache__" -exec rm -rf {} +

.PHONY: cp
cp:
	mkdir -p ${DEPLOY_PACKAGE}
	cp -r src/* ${DEPLOY_PACKAGE}/
	cp -r packages ${DEPLOY_PACKAGE}/packages/
	cp -r IPAexfont00401 ${DEPLOY_PACKAGE}/IPAexfont00401/
	cp -r json_data ${DEPLOY_PACKAGE}/json_data/
	cp config.json ${DEPLOY_PACKAGE}/

.PHONY: run
run: clean cp
	cd ${DEPLOY_PACKAGE} && python3 main.py

.PHONY: zip
zip: clean cp
	cd ${DEPLOY_PACKAGE} && zip -r ../lambda.zip .
	make clean

.PHONY: deploy
deploy: zip
	cd terraform && terraform apply
