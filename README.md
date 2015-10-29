# Where Should We Eat?

This project sets up a restaurant listing website.


## Table of contents

* [Program installation](#installation)
* [Database setup](#database-setup)
* [Creator](#creator)
* [Copyright and license](#copyright-and-license)


## Installation

For starters, you need [Python](https://www.python.org/downloads/). The program was written for Python 2.7, so that's what you should download and install. You may already have Python, especially if you're on a Mac or Linux machine. To check, open a Terminal window (on a Mac, use the Spotlight search and type in "Terminal"; on a PC go to Start > Run and type in "cmd") and type "python" at the prompt. You should get something that looks like this (run on my Mac):

```
Python 2.7.10 (v2.7.10:15c95b7d81dc, May 23 2015, 09:33:12)
[GCC 4.2.1 (Apple Inc. build 5666) (dot 3)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>>
```

Note the version number (2.7.10 in this case). If it starts with "3.", you should download version 2.7. If you have questions about any of this, check Python's [excellent online documentation](https://www.python.org/doc/).

There are a number of Python module dependencies for this project. To install them all, run the following:

```
pip install -r requirements.txt
```

Finally, you'll need [git](http://git-scm.com/download) so that you can clone this project.


## Database setup

The project user Sqlite as a database. To set it up, just run:

```
python database_setup.py
```

The file lotsofmenusandusers.py contains test data. To load it into the database, run:

```
python lotsofmenusandusers.py
```


## Creator

This program was built by me, Chris Willey, as part of the Udacity Nanodegree program for [Full Stack Developer](https://www.udacity.com/course/full-stack-web-developer-nanodegree--nd004).


## Copyright and License

Code and documentation copyright 2015 Christopher Willey. Code released under the MIT license.