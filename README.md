# LinkUp 

LinkUp is a free novel software alternative to the Doodle website.
LinkUp solves the inflexible solutions found in Doodle, with an improved algorithmic solution (combining intuitive design and functionality) that focuses on enhancing efficiency, productivity, well-being and reducing cognitive load.
# How to install and run locally?

1. Install a virtual environment such as [conda](https://conda.io/en/latest/miniconda.html)
	a. Create a virtual environment with Python 3.6 (Refer to [cheat sheet in case stuck](https://docs.conda.io/projects/conda/en/4.6.0/_downloads/52a95608c49671267e40c689e0bc00ca/conda-cheatsheet.pdf))
	b. Activate the environment 
```sh
$ WINDOWS: activate environmentname 
$ LINUX, macOS: source activate environmentname
```
2. **pip install** -r **requirements**.**txt** : This is the phase where necessary components of the app are installed 
3. **python manage.py makemigrations**
4. **python manage.py runserver** : runs the app
5. **open [http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

Notes: localhost version please use SQLite, it may need configuration of API keys too.

# Release Information
24.04.19: Public Release: First stable release, group feature and calendar intergration has been missed out of stable release due to time constraints. 

## Tech

LinkUp uses a number of open source projects to work properly:

* [AngularJS] - HTML enhanced for web apps!
* [Ace Editor] - awesome web-based text editor
* [markdown-it] - Markdown parser done right. Fast and easy to extend.
* [Bootstrap] - great UI boilerplate for modern web apps
* [node.js] - evented I/O for the backend
* [Express] - fast node.js network app framework [@tjholowaychuk]
* [Gulp] - the streaming build system
* [Breakdance](http://breakdance.io) - HTML to Markdown converter
* [jQuery] - duh

## Functional Requirements Implementation Overview
Primary Functional Requirments

| No |Function | Requirment Description | Implemented (Yes/No) ?  |
| :------------ |:----:| -:|-----:|
|1| Authentication|All Users can register, login, reset their password and log out of web application. |Yes |
|2| Authentication|Database stores individual entries of username, password, name and email. | Yes |
|3|Authentication |Sign up page implements Captcha to verify human sign up and prevent bots. | Yes | 
|4|Authentication (Cookies) |Upon signup users’ input is valid to ensure valid and accurate accounts are created. | Yes | 
|5|Feature (Dashboard) |The system tracks cookies and sessions to ensure the right users have access the right page. Example: right event/poll page. | Yes | 
|6|Feature (Dashboard) |Sign up page implements Captcha to verify human sign up and prevent bots. | Yes | 
|7|Feature (Event Scheduling) |Sign up page implements Captcha to verify human sign up and prevent bots. | Yes | 
|8|Feature (Event Scheduling) |The system uses an algorithm to automatically determine and display the best optimal option for event initiator based on options (DateTime & Locations). | Yes | 
|9|Feature (Event Scheduling) |All Users can create public events specifying the title, description, category event fits, importance, DateTime choices and location choices. | Yes | 
|10|Feature (Event Scheduling) |Registered users can create private events as well as invite event participants/ friends through username. | Yes | 
|11|Feature (Event Scheduling) |All Users can choose preferred options and indicate their availability for an event based on proposed options set out by event initiator. | Yes | 
|12|Feature (Event Scheduling) |Event Participants join an event either through an available link or invited through their username. | Yes | 
|13|Feature (Event Scheduling) |Initiator based on results can choose the final option based on computations and notify participants.. | Yes | 




