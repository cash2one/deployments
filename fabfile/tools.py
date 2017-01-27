"""
This module contains all the tasks to get a new or exisiting
server up and running
"""

from fabric.api import cd, env, puts, run
from fabric.colors import green, red, yellow

from fabfile import git

LETSENCRYPT_DOWNLOAD = 'https://github.com/letsencrypt/letsencrypt'
LETSENCRYPT_DIR = '/var/letsencrypt'

domains = ' '.join(['-d {}'.format(domain) for domain in env.DOMAINS])


def apt_get_install(debs):
    """
    Use apt-get to install prerequisites packages necessary
    for the server to run. Use python join method to concatenate
    multiple packages in the @debs list.
    """
    puts(yellow('Starting installation of prerequisite packages'))
    run('apt-get --assume-yes install {}'.format(' '.join(debs)))


def set_shell_to_zsh():
    """
    Set the default shell to zsh
    """
    puts(yellow('Installing OhMyZsh theme and setting zsh to default shell'))
    run('curl -L http://install.ohmyz.sh | sh')


def prep_gulp(repo_path, npm_debs):
    """
    Install gulp and all its dependencies using npm.
    Run gulp to generate the CSS static file.
    """
    puts(green('Installing gulp and its dependencies using npm(node package manager)'))
    with cd(repo_path):
        run('npm install {}'.format(' '.join(npm_debs)))
        run('npm install -g bower gulp')
        run('bower install bourbon --allow-root')
        run("gulp production")


def prep_requirements(requirements_file_path):
    """"
    Install all required pip dependencies on server
    """
    puts(yellow('Installing python package dependencies'))
    run('pip install -r {}'.format(requirements_file_path))


def create_directory(path):
    """
    Create directory. If the path doesn't exist, will create it.
    """
    puts(green('Creating website home directory'))
    run('mkdir -p {}'.format(path))


def install_letsencrypt():
    """
    Enable HTTPS and SSL on Nginx
    """
    puts(red('Starting Installation of letsencrypt to enable HTTPs and SSL on Nginx'))
    with cd('/var'):
        run('rm -rf letsencrypt')
        git.fetch_clean_repo(LETSENCRYPT_DOWNLOAD)

    with cd(LETSENCRYPT_DIR):
        run('chgrp www-data /usr/share/nginx/html/')
        run('./letsencrypt-auto certonly -a webroot --webroot-path=/usr/share/nginx/html {}'.format(domains))

        # Generate a 2048-bit cert
        run('openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048')


def sed_replace(regex, replacement, file_path):
    """
    Replace all instances of @regex with @replacement in the given @file_path.
    """
    puts(yellow('Replacing all instances of {} with {} in {}'.format(regex, replacement, file_path)))
    run('sed -i \'s/{}/{}/g\' {}'.format(regex, replacement, file_path))
