"""
Base Task for all server deploys.
"""

from fabric.api import cd, env, execute, run, sudo
from fabric.contrib.files import exists
from fabric.tasks import Task

import git
import nginx
import tools


class Base(Task):
    """
    Base Task to install basic server requirements
    """
    name = "prep_server"
    APT_DEBS = (
        'git-core',
        'gzip',
        'nginx',
        'python-pip',
        'rsync',
        'sendmail',
        'zsh',
    )

    def run(self, git_branch='master'):
        """
        Run Base task
        """

        # Housekeeping
        run('apt-get clean')
        run('apt-get update')

        tools.apt_get_install(self.APT_DEBS)

        tools.set_shell_to_zsh()

        with cd(env.REPO_DIR):
            sudo('rm -rf %s' % env.OPS_DIR)
            git.fetch_clean_repo(env.REPO_URL)

        execute(nginx.Nginx())
BASE = Base()
