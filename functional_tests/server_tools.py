from fabric.api import run
from fabric.context_managers import settings

def _get_manage_dot_py(host):
    cmd = '/home/pi/sites/{}/virtualenv/bin/python'.format(host)
    arg = '/home/pi/sites/{}/source/manage.py'.format(host)
    return cmd + ' ' + arg

def reset_database(host):
    manage_dot_py = _get_manage_dot_py(host)
    with settings(host_string='pi@{}'.format(host)):
        run('{} flush --noinput'.format(manage_dot_py))

def create_session_on_server(host, email):
    manage_dot_py = _get_manage_dot_py(host)
    with settings(host_string='pi@{}'.format(host)):
        session_key = run('{} create_session {}'.format(manage_dot_py, email))
        return session_key.strip()
