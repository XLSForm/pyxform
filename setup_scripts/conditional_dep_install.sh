: '
Detects python version and makes situational installs.
'

pip install pipenv

pipenv install 
pipenv install --dev

mainv=`python -c 'import sys; print(sys.version_info[0])'`
subv=`python -c 'import sys; print(sys.version_info[1])'`

if [ $mainv -eq 2 ]; then
    echo "python 2 detected."
    echo 'python version is < 3.2, we need functools32 and older pylint'
    pipenv install pylint==1.9.4 
    pipenv install functools32==3.2.3.post2 
else
    echo "python 3 detected."
    if [ $subv -lt 3 ]; then
        echo 'python version is < 3.2, need functools32 and older pylint'
        pipenv install pylint==1.9.4 
        pipenv install functools32==3.2.3.post2 
    fi
    if [ $subv -gt 5 ]
    then
	echo "python version is > 3.6, we can support black"
    	pip3 install black 
    fi
fi
