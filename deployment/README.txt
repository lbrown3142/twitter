Production setup

See http://www.djangobook.com/en/2.0/chapter12.html
for things to do for production, e.g. Turn off Debug = true in settings.py

Python/Pip:
	sudo apt-get install python-pip python-dev build-essential
	sudo pip install virtualenv
	sudo pip install --upgrade pip

Java:
	sudo add-apt-repository -y ppa:webupd8team/java
	sudo apt-get update
	sudo apt-get -y install oracle-java8-installer

Elastic Search:
	# See: https://www.digitalocean.com/community/tutorials/how-to-install-elasticsearch-logstash-and-kibana-elk-stack-on-ubuntu-14-04

	wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
	echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | sudo tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
	sudo apt-get update
	sudo apt-get -y install elasticsearch

	# Configure elastic search
	sudo vim /etc/elasticsearch/elasticsearch.yml
		-> network.host: localhost

    # Limit memory usage:
		/etc/security/limits.conf:
			elasticsearch - nofile 65535
			elasticsearch - memlock unlimited

		/etc/default/elasticsearch:
			ES_HEAP_SIZE=128m
			MAX_OPEN_FILES=65535
			MAX_LOCKED_MEMORY=unlimited

		/etc/elasticsearch/elasticsearch.yml:
			bootstrap.mlockall: true

	sudo service elasticsearch restart
	sudo update-rc.d elasticsearch defaults 95 10


	sudo service elasticsearch restart
	sudo update-rc.d elasticsearch defaults 95 10

Kibana:
	sudo groupadd -g 998 kibana
	sudo useradd -u 998 -g 998 kibana
	cd ~; wget https://download.elastic.co/kibana/kibana/kibana-4.3.1-linux-x64.tar.gz
	tar xvf kibana-*.tar.gz

	# configure
	vim ~/kibana-4*/config/kibana.yml
		-> server.host: "localhost"

	sudo mkdir -p /opt/kibana
	sudo cp -R ~/kibana-4*/* /opt/kibana/
	sudo chown -R kibana: /opt/kibana

	cd /etc/init.d && sudo curl -o kibana https://gist.githubusercontent.com/thisismitch/8b15ac909aed214ad04a/raw/fc5025c3fc499ad8262aff34ba7fde8c87ead7c0/kibana-4.x-init

	cd /etc/default && sudo curl -o kibana https://gist.githubusercontent.com/thisismitch/8b15ac909aed214ad04a/raw/fc5025c3fc499ad8262aff34ba7fde8c87ead7c0/kibana-4.x-default

	sudo chmod +x /etc/init.d/kibana
	sudo update-rc.d kibana defaults 96 9
	sudo service kibana start

# Nginx reverse proxy
	sudo apt-get install nginx apache2-utils
	sudo htpasswd -c /etc/nginx/htpasswd.users kibanaadmin
	# password set to "Capgemini1"

	sudo vim /etc/nginx/sites-available/default
	# Replace contents with (type dG to delete contents, then i, then right-click paste):
	server {
	    listen 8000;

	    server_name example.com;

	    auth_basic "Restricted Access";
	    auth_basic_user_file /etc/nginx/htpasswd.users;

	    location / {
		proxy_pass http://localhost:5601;
		proxy_http_version 1.1;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection 'upgrade';
		proxy_set_header Host $host;
		proxy_cache_bypass $http_upgrade;        
	    }
	}

	sudo service nginx restart

	# Should now be able to browse to hostname:81 and see kibana


# Now create the virtualenv
	virtualenv -p python3 twitter
	cd twitter
	source bin/activate

# Git
	sudo apt-get install git

	git clone https://github.com/lbrown3142/twitter.git twitter 
	# user: lewis.brown@capgemini.com
	# pwd: Iam24yearsold

# We now should have our requirements.txt file in the twitter folder. Install dependencies:
pip install -r requirements.txt


# Install MySql
	# See https://www.linode.com/docs/databases/mysql/how-to-install-mysql-on-ubuntu-14-04

	sudo apt-get install mysql-server
	# Set root password to Capgemini1

	sudo mysql_secure_installation
	# Answer yes to all options

	sudo apt-get install libmysqlclient-dev
	sudo apt-get install python-mysqldb

	sudo apt-get install python3-dev
	pip install mysqlclient
		# doing a sudo pip here installs into global python2.7 for some reason?

	sudo pip install MySQL-python

	# Set utf8 default character set
	sudo vim /etc/mysql/my.cnf
		[client]
		default-character-set=utf8

		[mysqld]
		character-set-server = utf8
		collation-server = utf8_unicode_ci
		init-connect='SET NAMES utf8'

		[mysql]
		default-character-set = utf8


	# Create a new database and user
	mysql -u root -p
	CREATE DATABASE twitter_db;

	# Add to settings.py
	DATABASES = {
	    'default': {
		'ENGINE': 'django.db.backends.mysql',
		'NAME': 'twitter_db',
		'USER': 'root',
		'PASSWORD': 'Capgemini1',
	    }
	}

	python manage.py migrate

	# Test that the app runs ok in dev mode (we configure Apache below)
	python manage.py runserver 0.0.0.0:8001

# Celery
	sudo apt-get install rabbitmq-server
	sudo pip install -U librabbitmq		

	# Get the /etc/init.d/celeryd init script from
	# https://github.com/celery/celery/blob/3.0/extra/generic-init.d/celeryd
	# and save into /etc/init.d/celeryd using vim

	# Make it executable
	cd /etc/init.d
	sudo chmod +x celeryd

	# Make it run on startup
	sudo update-rc.d celeryd defaults
	sudo update-rc.d celeryd enable

	# Make it owned by root and have the correct permissions
	sudo chown root:root celeryd
	sudo chmod 777 celeryd

	# Create virtualenv version of /etc/default/celeryd:
	sudo vim /etc/default/celeryd

		# Name of nodes to start, here we have a single node
		CELERYD_NODES="worker"
		# or we could have three nodes:
		#CELERYD_NODES="w1 w2 w3"

		# Where to chdir at start.
		CELERYD_CHDIR="/home/ubuntu/twitter/twitter"

		# Python interpreter from environment.
		ENV_PYTHON="$CELERYD_CHDIR/../bin/python"

		# How to call "manage.py celeryd_multi"
		CELERYD_MULTI="$ENV_PYTHON $CELERYD_CHDIR/manage.py celeryd_multi"

		# How to call "manage.py celeryctl"
		CELERYCTL="$ENV_PYTHON $CELERYD_CHDIR/manage.py celeryctl"

		# Extra arguments to celeryd
		CELERYD_OPTS="--time-limit=300 --concurrency=3"

		# Name of the celery config module.
		CELERY_CONFIG_MODULE="celeryconfig"

		# %n will be replaced with the nodename.
		CELERYD_LOG_FILE="/var/log/celery/%n.log"
		CELERYD_PID_FILE="/var/run/celery/%n.pid"

		# Workers should run as an unprivileged user.
		CELERYD_USER="celery"
		CELERYD_GROUP="celery"

		# Name of the projects settings module.
		export DJANGO_SETTINGS_MODULE="twitter.settings"

		# If enabled pid and log directories will be created if missing,
		# and owned by the userid/group configured.
		CELERY_CREATE_DIRS=1

	# Create the celery unprivileged user (password celery)
	    sudo adduser celery
	    sudo mkdir /var/run/celery
	    sudo chown celery /var/run/celery
	    sudo chgrp celery /var/run/celery	
	    sudo mkdir /var/log/celery
	    sudo chown celery /var/log/celery
	    sudo chgrp celery /var/log/celery

	# Check that the celery daemon can be started manually
	sudo /etc/init.d/celeryd start
	sudo /etc/init.d/celeryd status

	# and then check that celery control shows it is working (in virtualenv)
	celery status
		-> worker@steve2: OK	# working ok

	# Then check it auto-starts on reboot
	(virtualenv) celery status  # should report worker thread


Configuring Apache
	See:
		https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/modwsgi/
		or
		https://www.digitalocean.com/community/tutorials/how-to-serve-django-applications-with-apache-and-mod_wsgi-on-ubuntu-14-04


	sudo apt-get install apache2 apache2-mpm-prefork apache2-utils libexpat1
	
	# install mod_wsgi
	sudo apt-get install libapache2-mod-wsgi-py3
		

	# Edit contents of /etc/apache2/sites-available/000-default.conf, setting the server name and correct paths to the django app:

	<VirtualHost *:80>
		# The ServerName directive sets the request scheme, hostname and port that
		# the server uses to identify itself. This is used when creating
		# redirection URLs. In the context of virtual hosts, the ServerName
		# specifies what hostname must appear in the request's Host: header to
		# match this virtual host. For the default virtual host (this file) this
		# value is not decisive as it is used as a last resort host regardless.
		# However, you must set it for any further virtual host explicitly.
		ServerName example.com

		ServerAdmin webmaster@localhost
		DocumentRoot /var/www/html

		# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
		# error, crit, alert, emerg.
		# It is also possible to configure the loglevel for particular
		# modules, e.g.
		#LogLevel info ssl:warn

		ErrorLog ${APACHE_LOG_DIR}/error.log
		CustomLog ${APACHE_LOG_DIR}/access.log combined

		Alias /static /home/ubuntu/twitter/twitter/static
	    <Directory /home/ubuntu/twitter/twitter/static>
		Require all granted
	    </Directory>

		<Directory /home/ubuntu/twitter/twitter/twitter>
		<Files wsgi.py>
		    Require all granted
		</Files>
	    </Directory>

		WSGIDaemonProcess myproject python-path=/home/ubuntu/twitter/twitter:/home/ubuntu/twitter/lib/python3.4/site-packages
	    WSGIProcessGroup myproject
	    WSGIScriptAlias / /home/ubuntu/twitter/twitter/twitter/wsgi.py

		#SetEnv DJANGO_SETTINGS_MODULE twitter.settings

		# For most configuration files from conf-available/, which are
		# enabled or disabled at a global level, it is possible to
		# include a line for only one particular virtual host. For example the
		# following line enables the CGI configuration for this host only
		# after it has been globally disabled with "a2disconf".
		#Include conf-available/serve-cgi-bin.conf
	</VirtualHost>

		# vim: syntax=apache ts=4 sw=4 sts=4 sr noet

	# Set permissions
	sudo chown :www-data /home/ubuntu/twitter/twitter

	sudo service apache2 restart

# Can monitor celery worker to see if it is doing any work:
tail -f /var/log/celery/worker.log

# Configure Kibana index
# Goto localhost:81
# Uncheck "Index contains time-based events
# Enter my_index


# Create log directory
sudo mkdir /var/log/capgemini
sudo chmod 777 /var/log/capgemini
