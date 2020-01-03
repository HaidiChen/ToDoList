from fabric.contrib.files import append, exists, sed
from fabric.api import env, local, run
import random

REPO_URL = 'https://github.com/haidichen/todolist.git'

def deploy():
    site_folder = '/home/{0}/sites/{1}'.format(env.user, env.host)
    source_folder = site_folder + '/source'
    _install_required_packages()
    _create_directory_structure_if_necessary(site_folder)
    _get_latest_source(source_folder)
    _update_settings(source_folder, env.host)
    _update_virtualenv(source_folder)
    _update_static_files(source_folder)
    _update_database(source_folder)
    if _is_first_time_deployment(env.host):
        _update_nginx_configuration(source_folder, env.host)
        _update_systemd_service(source_folder, env.host)
        _reload_daemon_and_nginx()
        _enable_and_start_service(env.host)
    else:
        _restart_service(env.host)

def _install_required_packages():
    run('sudo apt-get install git nginx python3 python3-venv -y')

def _create_directory_structure_if_necessary(site_folder):
    for subfolder in ('database', 'static', 'virtualenv', 'source'):
        run('mkdir -p {0}/{1}'.format(site_folder, subfolder))

def _get_latest_source(source_folder):
    if exists(source_folder + '/.git'):
        run('cd {} && git fetch'.format(source_folder))
    else:
        run('git clone {0} {1}'.format(REPO_URL, source_folder))
    current_commit = local('git log -n 1 --format=%H', capture=True)
    run('cd {0} && git reset --hard {1}'.format(source_folder, current_commit))

def _update_settings(source_folder, site_name):
    settings_path = source_folder + '/superlists/settings.py'
    sed(settings_path, 'DEBUG = True', 'DEBUG = False')
    sed(
            settings_path, 
            'ALLOWED_HOSTS = .+$',
            'ALLOWED_HOSTS = ["{}"]'.format(site_name)
        )
    secret_key_file = source_folder + '/superlists/secret_key.py'
    if not exists(secret_key_file):
        chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
        key = ''.join(random.SystemRandom().choice(chars) for _ in range(50))
        append(secret_key_file, 'SECRET_KEY = "{}"'.format(key))
    append(settings_path, '\nfrom .secret_key import SECRET_KEY')

def _update_virtualenv(source_folder):
    virtualenv_folder = source_folder + "/../virtualenv"
    if not exists(virtualenv_folder + '/bin/pip'):
        run('python3 -m venv {}'.format(virtualenv_folder))
    run('{0}/bin/pip install -r {1}/requirements.txt'.format(virtualenv_folder,
            source_folder)
        )

def _update_static_files(source_folder):
    run(
        'cd {0} && ../virtualenv/bin/python '  
        'manage.py collectstatic --noinput'.format(source_folder)
        )

def _update_database(source_folder):
    run(
            'cd {0} && ../virtualenv/bin/python '
            ' manage.py migrate --noinput'.format(source_folder)
            )

def _is_first_time_deployment(site_name):
    systemd_path = '/etc/systemd/system/gunicorn-{}.service'.format(site_name)
    if exists(systemd_path):
        return False
    return True

def _update_nginx_configuration(source_folder, site_name):
    conf_path = source_folder + '/deploy_tools/nginx.template.conf'
    temp_conf_path = source_folder + '/{}'.format(site_name)
    deploy_conf_path = '/etc/nginx/sites-available/{}'.format(site_name)
    run('cp {} {}'.format(conf_path, temp_conf_path))
    sed(temp_conf_path, 'SITENAME', site_name)
    run('sudo mv {} {}'.format(temp_conf_path, deploy_conf_path))
    symlink_conf_path = '/etc/nginx/sites-enabled/{}'.format(site_name)
    if exists(symlink_conf_path):
        run('sudo rm {}'.format(symlink_conf_path))
    run('sudo ln -s {} {}'.format(deploy_conf_path, symlink_conf_path))

def _update_systemd_service(source_folder, site_name):
    conf_path = source_folder + '/deploy_tools/gunicorn-systemd.template.service'
    temp_conf_path = source_folder + '/{}.service'.format(site_name)
    run('cp {} {}'.format(conf_path, temp_conf_path))
    sed(temp_conf_path, 'SITENAME', site_name)
    systemd_path = '/etc/systemd/system/gunicorn-{}.service'.format(site_name)
    run('sudo mv {} {}'.format(temp_conf_path, systemd_path))

def _reload_daemon_and_nginx():
    run('sudo systemctl daemon-reload')
    run('sudo systemctl reload nginx')

def _enable_and_start_service(site_name):
    run('sudo systemctl enable gunicorn-{}'.format(site_name))
    run('sudo systemctl start gunicorn-{}'.format(site_name))

def _restart_service(site_name):
    service_name = 'gunicorn-{}.service'.format(site_name)
    run('sudo systemctl restart {}'.format(service_name))
