
clean:
	find . -name "*.pyc" -exec rm -rf {} \;
run:
	python manage.py runserver 127.0.0.1:8000
migrate:
	python manage.py migrate
migrations:
	python manage.py makemigrations
user:
	python manage.py createsuperuser
lint:
	flake8 documentsManager/
shell:
	python manage.py shell
test:
	coverage run  manage.py test --no-input --failfast --keepdb && coverage report -m  --skip-covered