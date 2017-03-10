import sys
reload(sys)
sys.setdefaultencoding('utf8')
import os
import site

# Virtualenv location (default: None)
virtualenv = None

if virtualenv is not None:
    virtualenv = virtualenv.rstrip('/')
    # Add the site-packages of the chosen virtualenv to work with
    #site.addsitedir("%s/lib/python2.7/site-packages" % (virtualenv,))
	# Activate your virtualenv
    activate_env="%s/bin/activate_this.py" % (virtualenv,)
    execfile(activate_env, dict(__file__=activate_env))

# App's root ../
app_root = (os.path.abspath(os.path.join(
                            os.path.dirname(__file__),
                            '..')))

# Add the app's directory to the PYTHONPATH
sys.path.append(app_root)

# Initialize WSGI Object
import nfw
nfw_wsgi = nfw.Wsgi(app_root)

# LETS GET THIS PARTY STARTED...
application = nfw_wsgi.application()

