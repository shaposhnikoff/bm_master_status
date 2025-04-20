#!/bin/sh


#../venv/bin/pip3 freeze > requirements.txt


dated=`date +%Y-%m-%d-%H%M%S`

git add .
echo run git push on ${dated}


for i in `git status | grep deleted | awk '{print $2}'`; do git rm $i; done

# git add -u .
#
# git commit -m 'some fix on '${dated} # nice ;-)
pre-commit run --all-files
git commit -m "$dated $(curl -s https://whatthecommit.com/index.txt)"
git push -u origin main
