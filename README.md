# EpiML

EpiML can detect main effect and epistatic effect features in your data by using several build-in machine learning methods and produce many interactive visualizations to help understand results. Especially for some case studies like SNP and miRNA data, external resources are embedded for epistasis analysis. 

An illustration of EpiML is shown in following:
![alt text](EpiMap/static/img/epiml.png)
*Figure 1. The workflow of epistasis web service. a. Our epistasis analysis server allows users describe their job, upload data and select a machine learning method for analysis. b. We provide interactive tools for visualizing and downloading results. c. Customize analysis. All automatically generated Jupyter notebooks and pre-configured Docker containers can be downloaded, modified and rerun, allowing users to fully customize their analysis code on local computers. d. Generate bioRxiv report that provides detailed information about the models.*

---------------------------------
Here is a quick tutorial to deploy a Flask application on Ubuntu 16.04LTS using Apache2 and mod-wsgi. 

Requirements
1.	A server running Ubuntu 16.04LTS.
2.	A non-root user account with sudo privilege set up on your server.

Install Packages:
We can install depended packages easily by using Ubuntu’s package manager, apt. 
1.	Apache2

The Apache HTTP Server Project is an effort to develop and maintain an open-source HTTP server for modern operating systems including UNIX and Windows. The goal of this project is to provide a secure, efficient and extensible server that provides HTTP services in sync with the current HTTP standards. Install apache2 using following command:

`sudo apt-get install apache2`

2.	mod-wsgi for python3

The Web Server Gateway Interface (WSGI) is a specification for simple and universal interface between web servers and web applications or frameworks for the Python programming language. Mod_wsgi is an Apache HTTP Server module that provides a WSGI compliant interface for hosting Python based web applications under Apache. It enables Apache to serve Flask applications.
sudo apt-get install libapache2-mod-wsgi-py3
After finished, the module wsgi should be enabled. If not, you can enable wsgi by using the following command:

`sudo a2enmod wsgi`

3.	Git
Git is a fast, scalable, distributed revision control system with an unusually rich command set that provides both high-level operations and full access to internals.

`sudo apt-get install git`

change the work directory, and clone our website from github.	

```
cd /var/www/
sudo git clone https://github.com/work-hard-play-harder/ShiLab.git
sudo chmod -R 777 ShiLab
```

4.	R
R is a free software environment for statistical computing and graphics. Install r-base and global packages by using following commands:

`sudo apt-get install r-base`

Install global R packages: glmnet, EBEN, jsonlite

```
sudo su - -c "R -e \"install.packages('glmnet', repos = 'http://cran.rstudio.com/')\""
sudo su - -c "R -e \"install.packages('EBEN', repos = 'http://cran.rstudio.com/')\""
sudo su - -c "R -e \"install.packages('jsonlite', repos = 'http://cran.rstudio.com/')\""
sudo su - -c "R -e \"install.packages('sets', repos = 'http://cran.rstudio.com/')\""
```

5.	Python3

Python is an easy to learn, powerful programming language. It has efficient high-level data structures and a simple but effective approach to object-oriented programming. Python’s elegant syntax and dynamic typing, together with its interpreted nature, make it an ideal language for scripting and rapid application development in many areas on most platforms. Python3 should be install in Ubuntu 16.04 LTS. But we still need to install the python package manager：

`sudo apt-get install python3-setuptools python3-pip`

6.	Virtualenv

Virtual environment is a self-contained directory tree that contains a Python installation for a particular version of Python, plus a number of additional packages.

`sudo pip3 install virtualenv`

create a virtual environment for website
```
cd /var/www/ShiLab
virtualenv venv
source venv/bin/activate
```

7.	Flask 0.12 and plugins, Scientific tools

Install flask by using following command in virtual environment:

`pip install -r requirements.txt`

Run the following command to test if the installation is successful:

`python run.py`

You should see the following output:

```
* Serving Flask app "EpiMap" (lazy loading)
 * Environment: production
   WARNING: Do not use the development server in a production environment.
   Use a production WSGI server instead.
 * Debug mode: on
 * Running on http://127.0.0.1:5000/ (Press CTRL+C to quit)
 * Restarting with stat
 * Debugger is active!
 * Debugger PIN: 734-373-964 (PIN should be different)
```

You can open a browser and input the address: http://127.0.0.1:5000/. If you see the web server, you have successfully run the website. 

`deactivate`

Configure New Virtualhost for Flask
Now, you will need to create a new wsgi and a new virtual host file for Flask App.

1.	Create a firstflaskapp.wsgi file inside the /var/www/ShiLab directory to serve the Flask App:

`nano ShiLab.wsgi`

Add the following content:
```python
#!/usr/bin/python3
import sys
import logging
import site

# Add the site-packages of the chosen virtualenv to work with
site.addsitedir('/var/www/ShiLab/venv/lib/python3.5/site-packages')

logging.basicConfig(stream=sys.stderr)
sys.path.insert(0,"/var/www/ShiLab/")

from EpiMap import app as application
```

2.	Now, you will create a new virtual host file for the Flask app so that it can run in apache2.

Change to the /etc/apache2/sites-available directory:

`cd /etc/apache2/sites-available`

Create the configure file for Flask App:

`sudo nano ShiLab.conf`

Add the following content:

```
<VirtualHost *:80>
        ServerName www.example.com
        ServerAdmin admin@example.com

        WSGIScriptAlias /ShiLab/EpiMap /var/www/ShiLab/ShiLab.wsgi
        <Directory /var/www/ShiLab/EpiMap/>
            Order allow,deny
            Allow from all
        </Directory>

        ErrorLog ${APACHE_LOG_DIR}/ShiLab/error.log
        LogLevel warn
        CustomLog ${APACHE_LOG_DIR}/ShiLab/access.log combined
</VirtualHost>
```

You need to create /var/log/apache2/ ShiLab directory to store the log file.

`sudo mkdir /var/log/apache2/ShiLab`

Editing your /etc/hosts file to review the domain example.com before you public it.

`sudo nano /etc/hosts`

Add a line in last:

`127.0.0.1       www.example.com`

Enable the virtual host with the following command. By the way, you also can disable the configure with a2dissite:

`sudo a2ensite ShiLab.conf`

Restart Apache to apply the changes

`sudo apachectl restart`

You maybe get a friendly warning: AH00558: apache2: Could not reliably determine the server's fully qualified domain name, using 127.0.1.1. Set the 'ServerName' directive globally to suppress this message. 
But don’t worry. The application has been enabled. 
