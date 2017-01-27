"""
Task to Configure Nginx on server
"""
from os.path import join, sep

from fabric.api import env, puts, run, sudo
from fabric.colors import green, red, yellow
from fabric.contrib.files import exists
from fabric.tasks import Task

import tools


class Nginx(Task):
    """
    Install Nginx on server
    """
    name = 'Install Nginx'

    nginx_dir = join(sep, 'etc', 'nginx')
    ops_nginx_dir = join(env.OPS_ETC_DIR, 'nginx')
    insecure_nginx_config = join(ops_nginx_dir, 'insecure_nginx.conf')
    secure_nginx_config = join(ops_nginx_dir, 'nginx.conf')
    ssl_config = join(ops_nginx_dir, 'ssl.conf')
    cron_file = join(env.REPO_DIR, 'deployments', 'ubuntu', 'etc', 'cron.d', 'ssl_cert_renewal')
    cron_config_path = join(sep, 'etc', 'cron.d')
    special_nginx_configs = join(ops_nginx_dir, 'special-*')

    def run(self):
        cert_file = join(sep, 'etc', 'letsencrypt', 'live', env.host, 'cert.pem')

        # Check if certificate files are present then skip copying over
        # nginx unsecure configuration
        if not exists(cert_file):
            puts(green('Cert file doesn\'t exist. Creating one.'))

            puts(yellow('Installing insecure intermediate Nginx config'))
            sudo('cp {} {}'.format(self.insecure_nginx_config, join(self.nginx_dir, 'nginx.conf')))

            # Replace INSERT_HOST_HERE instaces with host name
            tools.sed_replace('INSERT_HOST_HERE', ' '.join(env.DOMAINS), join(self.nginx_dir, 'nginx.conf'))

            sudo('service nginx restart')

            # Does a lot. Installs SSL certs with Let's Encrypt and reconfigures Nginx.
            puts(yellow('Starting Let\'s Encrypt install.'))
            tools.install_letsencrypt()

            puts(yellow('Copying cron to refresh certificate.'))
            sudo('cp {} {}'.format(self.cron_file, self.cron_config_path))

        else:
            # Print out expiration date of SSL Certificates
            puts(red('Certificate exists: skipping certificate creation'))
            sudo('echo | openssl s_client -connect {}:443 2>/dev/null | openssl x509'
                ' -in {} -noout -dates'.format(env.host, cert_file))

        # Upload real Nginx configs
        puts(yellow('Installing secure Nginx configs.'))
        sudo('cp {} {}'.format(self.special_nginx_configs, self.nginx_dir))
        sudo('cp {} {}'.format(self.ssl_config, self.nginx_dir))
        sudo('cp {} {}'.format(self.secure_nginx_config, self.nginx_dir))

        # Replace INSERT_HOST_HERE instances with host name
        tools.sed_replace('INSERT_HOST_HERE', env.host, join(self.nginx_dir, 'nginx.conf'))
        tools.sed_replace('INSERT_HOST_HERE', env.host, join(self.nginx_dir, 'ssl.conf'))

        sudo('service nginx restart')
