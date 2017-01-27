"""
This module downloads, configures and installs Wordpress.
"""

from os.path import join

from fabric.api import cd, env, execute, put, puts, run, task
from fabric.colors import green, red, yellow
from fabric.tasks import Task

from fabfile import base, git, nginx, tools

DEFAULT_DATABASE_NAME = 'sergedb'

REMOTE_ROOT = join(env.TMP_PATH, 'wordpress')
REMOTE_DOWNLOAD = 'https://wordpress.org/latest.tar.gz'
REMOTE_ROOT_PATH = join(env.WWW_DIR, 'wordpress')
REMOTE_SQL_DUMP_NAME = join(env.TMP_PATH, 'dump_file.sql')
REMOTE_UPLOADS_PATH = join(REMOTE_ROOT_PATH, 'wp-content', 'uploads')

THEME_DIR = join(env.REPO_DIR, 'themes')
REMOTE_THEME_DIR = join(REMOTE_ROOT_PATH, 'wp-content', 'themes')


class Deploy(Task):
    """
    Deploy a wordpress site to a new or existing server
    Pass the name of the branch to deploy from through
    the command like so wordpress.deploy:git_branch_name
    If any branch
    """
    name = "deploy"

    REMOTE_DEBS = (
        'mysql-server',
        'php5',
        'php5-common',
        'php5-cli',
        'php5-fpm',
        'php5-mysql',
        'python-pip',
    )

    def run(self, git_branch='master'):
        """
        Run wordpress deploy class
        """
        execute(base.Base(), git_branch)

        setup_mysql_to_skip_interactive_mode()

        tools.apt_get_install(self.REMOTE_DEBS)

        prep_database()

        tools.create_directory(env.WWW_DIR)
        with cd(env.WWW_DIR):
            download_wordpress()
            with cd(REMOTE_ROOT_PATH):
                configure_wordpress()

        execute(nginx.Nginx())


class InstallTheme(Task):
    """
    Install a theme from the repo into the WordPress theme dir.
    """
    name = "install_theme"

    def run(self, git_branch='master'):
        """
        Install theme to WordPress theme dir.
        """
        with cd(env.REPO_DIR):
            git.git_pull(git_branch)

        run('rsync -avLP {} {}'.format(THEME_DIR, REMOTE_THEME_DIR))


def configure_wordpress():
    """
    Create uploads folder and assign correct permissions.

    TODO: Permissions needs work.
    """
    puts(red('Configuring Wordpress: Assigning correct permissions; Creating uploads folder'))
    run('chown -R www-data:www-data {}'.format(REMOTE_ROOT_PATH))
    run('usermod -a -G www-data www-data')
    run('mkdir -p {}'.format(REMOTE_UPLOADS_PATH))
    run('chown -R :www-data {}'.format(REMOTE_UPLOADS_PATH))


def download_wordpress():
    """
    Download and untar the downloaded file.
    """
    puts(yellow('Downloading wordpress'))
    run('rm -rf {}/latest.tar.gz'.format(env.TMP_PATH))
    run('wget {} -P {}'.format(REMOTE_DOWNLOAD, env.TMP_PATH))
    run('tar -xvzf {}/latest.tar.gz -C {}'.format(env.TMP_PATH, env.WWW_DIR))


def setup_mysql_to_skip_interactive_mode():
    """
    Install MySQL Server in a Non-Interactive mode. Default root password will be "root"
    """
    puts(green('Setting root password to disable non-interactive mode'))
    run('echo "mysql-server mysql-server/root_password password jesus" | sudo debconf-set-selections')
    run('echo "mysql-server mysql-server/root_password_again password jesus" | sudo debconf-set-selections')


def prep_database(db_name=DEFAULT_DATABASE_NAME):
    """
    Configure database by creating the databse user and assigning all privileges to the user.
    """
    puts(yellow('Setting up mysql'))
    run('touch /var/run/mysqld/mysqld.sock')
    run('chown -R mysql:mysql /var/run/mysqld/')
    run('service mysql restart')
    run('mysql -u root --password="jesus" -e "CREATE DATABASE IF NOT EXISTS {}"'.format(db_name))
    run('mysql -u root --password="jesus" -e "GRANT ALL ON {0}.* to \'{0}\' IDENTIFIED BY \'{0}\'"'.format(db_name))
    run('mysql -u root --password="jesus" -e "FLUSH PRIVILEGES"')
    run("service mysql restart")


@task
def load_existing_db(db_name, dump_file_path):
    """
    This task loads a database dump file into a newly created database.
    """
    put(dump_file_path, REMOTE_SQL_DUMP_NAME)
    run('mysql {} < {}'.format(db_name, REMOTE_SQL_DUMP_NAME))
