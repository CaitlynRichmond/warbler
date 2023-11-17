# Warbler - Fullstack Twitter clone
Warbler is a Twitter clone. It is currently built as a multi-page application using server-side rendering with Jinja. The main goal of this project was to get comfortable with writing a backend in flask, with a focus on writing tests for certain portions of the code.

View the deployed site [here](https://warbler-r-us.onrender.com/), deployed with Render.

Login: tuckerdiane | Password: password

## Tech Stack
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/flask-%23000.svg?style=for-the-badge&logo=flask&logoColor=white)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Jinja](https://img.shields.io/badge/jinja-white.svg?style=for-the-badge&logo=jinja&logoColor=black)

## Features
Here is an overview of some of the key features

- Users are able to create accounts, log in, and sign up
- Users are able to send warbles, like the warbles of other users, and delete their own warbles
- Users are able to follow + unfollow other users, as well as view a list of who is following them
- Users are able to update their profile, including selecting a new profile picture
- Sessions are used to persist users logged in state
- 99% test coverage with super

## Local setup instructions
Fork and clone this repo

from the root folder of your forked repo

1.) Create the virtual environment and install the requirements using the following terminal commands:
```
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```
2.) Set up your local database (this assumes you have Postgres installed, if not, you can find instructions [here](https://www.postgresql.org/download/)

```
psql
CREATE DATABASE warbler;
(ctrl+D)
python3 seed.py
```
3.) Setup environment variables in .env
- create a .env file at the root of the project
- copy and paste the following code into your new .env file
  ```
  SECRET_KEY=secret
  DATABASE_URL=postgresql:///warbler
  ```

4.) Run the development server.
```
flask run -p 5001
```
Flask defaults to port 5000, however, many MacOS devices use port 5000 for airplay.

Warbler will now be viewable on localhost:5001


## Tests
- Warbler currently has 99% test coverage

to run the tests
```
python -m unittest
```



## Acknowledgements
Warbler was built during my time at Rithm School, as part of a 3-day sprint. My partner on the backend was [Logan Winnie](https://github.com/loganwinnier)