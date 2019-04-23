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

## Functional  Requirements Implementation Overview
#### Primary Functional Requirments

| No |Function | Requirment Description | Implemented (Yes/No) ?  |
| :------------ |:----:| -:|-----:|
|1| Authentication|All Users can register, login, reset their password and log out of web application. |Yes |
|2| Authentication|Database stores individual entries of username, password, name and email. | Yes |
|3|Authentication |Sign up page implements Captcha to verify human sign up and prevent bots. | Yes | 
|4|Authentication|Upon signup users’ input is valid to ensure valid and accurate accounts are created. | Yes | 
|5|Authentication(Cookies) |The system tracks cookies and sessions to ensure the right users have access the right page. Example: right event/poll page. | Yes | 
|6|Feature (Dashboard) |Registered Users can log in into their specific profile dashboard to view open events, events they initiated, closed events and vice versa for polls (secondary). | Yes | 
|7|Feature (Dashboard) |A registered user can import their calendar (E.G Google Calendar) to display their DateTime availability. After importing calendar, the user can then share and show their calendar schedule on their profile enabling potential participants the benefit of booking events quickly and with accuracy. | No | 
|8|Feature (Event Scheduling) |The system uses an algorithm to automatically determine and display the best optimal option for event initiator based on options (DateTime & Locations). | Yes | 
|9|Feature (Event Scheduling) |All Users can create public events specifying the title, description, category event fits, importance, DateTime choices and location choices. | Yes | 
|10|Feature (Event Scheduling) |Registered users can create private events as well as invite event participants/ friends through username. | Yes | 
|11|Feature (Event Scheduling) |All Users can choose preferred options and indicate their availability for an event based on proposed options set out by event initiator. | Yes | 
|12|Feature (Event Scheduling) |Event Participants join an event either through an available link or invited through their username. | Yes | 
|13|Feature (Event Scheduling) |Initiator based on results can choose the final option based on computations and notify participants.. | Yes | 

### Secondary Functional Requirments

| No        | Function           | Requirment Description  |  Implemented (Yes/No) ?   |
| ------------- |:-------------:| -----:| -----:|
| 1     | Feature (Poll) | LinkUp will extend capabilities offering users simple and effective polling solution allowing users to create, update, close and view public and private polls. | Yes |
| 2      | Feature(Dashboard)|   Registered users will be able to customise their profile in various actions such as uploading a profile image to be easily recognisable to make it more personable as well as having the ability to group users/contacts into groups improving the overall process of multiple user interaction. | Yes |
| 3 | Feature(Event Scheduling & Polls)|   With the implementation of an email delivery service such as SendGrid, Users can receive email updates on either event or polls.   | Yes |
| 4 | Feature(Event Scheduling)|  Event participants can mark themselves unavailable for events. If the unavailable option selected is greater than proposed options set by the initiator, then event participants have further capabilities to suggest new options for event organiser/initiator to consider. | No |
