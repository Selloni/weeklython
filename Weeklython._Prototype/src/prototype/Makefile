all:
	python3 s21_bookbot.py 

git:
	git add *
	git status
	git commit -m "$m"
	git push origin develop

db:
	rm s21_bookbot.db
	cp backup_s21_bookbot.db s21_bookbot.db

dbcp:
	rm backup_s21_bookbot.db
	cp s21_bookbot.db backup_s21_bookbot.db 