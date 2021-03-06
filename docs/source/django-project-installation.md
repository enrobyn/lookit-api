# Django Project Local Installation

This is the codebase for Experimenter and Lookit.  Experimenter is a platform for designing and administering research studies, meant for researchers. The Lookit platform is participant-facing, where users can signup and take part in studies. It is built using Django, PostgreSQL, and Ember.js (see Ember portion of codebase, [ ember-lookit-frameplayer](https://github.com/CenterForOpenScience/ember-lookit-frameplayer)), and is developed by the [Center for Open Science](https://cos.io/).

## Note: These instructions are for Mac OS.

### Prerequisites
- Make sure you have python 3.6: `$ python --version`.  If you don't have this, install from https://www.python.org/.
- Make sure you have `pip`. `$ pip --version`
- Create a virtual environment with python 3.6
  - One way to do this:
  - `$  pip install virtualenv`
  - `$ virtualenv -p python3 envname`, *where `envname` is the name of your virtual environment.*
  - `$ source envname/bin/activate` *Activates your virtual environment*
- Install postgres
  - make sure you have brew `$ brew`
  - `$ brew install postgresql`
  - `$ brew services start postgres` *Starts up postgres*
  - `$ createdb lookit` *Creates lookit database*

### Installation
- `$ git clone https://github.com/CenterForOpenScience/lookit-api.git`
- `$ cd lookit-api`
- `$ sh up.sh` *Installs dependencies and run migrations*
- `$ python manage.py createsuperuser` *Creates superuser locally (has all user permissions)*
- `$ touch project/settings/local.py` Create a local settings file.
- Add DEBUG = True to `local.py` and save. This is for local development only.
- `$ python manage.py runserver` *Starts up server*

### Handling video

This project includes an incoming webhook handler for an event generated by the Pipe
video recording service when video is transferred to our S3 storage. This requires a 
webhook key for authentication. It can be generated via our Pipe account and, for local
testing, stored in project/settings/local.py as `PIPE_WEBHOOK_KEY`. However, Pipe will
continue to use the handler on the production/staging site unless you edit the settings to 
send it somewhere else (e.g., using ngrok to send to localhost for testing). 

### Common Issues

During the installation phase, when running `sh up.sh`, you may see the following:
```
psql: FATAL:  role "postgres" does not exist
```
To fix, run something like the following from your home directory:
```
$../../../usr/local/Cellar/postgresql/9.6.3/bin/createuser -s postgres
```
If your version of postgres is different than 9.6.3, replace with the correct version above.
Running this command should be a one-time thing.

<hr>

You might also have issues with the installation of `pygraphviz`, with errors like

```
running install
Trying pkg-config
Package libcgraph was not found in the pkg-config search path.
Perhaps you should add the directory containing `libcgraph.pc'
to the PKG_CONFIG_PATH environment variable
No package 'libcgraph' found
```
or
```
pygraphviz/graphviz_wrap.c:2954:10: fatal error: 'graphviz/cgraph.h' file not found
#include "graphviz/cgraph.h"
       ^
1 error generated.
error: command 'clang' failed with exit status 1
```

To fix, try running something like:
```
$ brew install graphviz
$ pip install --install-option="--include-path=/usr/local/include" --install-option="--library-path=/usr/local/lib" pygraphviz
```
Then run `sh up.sh again.`
