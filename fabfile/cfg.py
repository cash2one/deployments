"""
Define generic constants for reusabililty
"""

from os.path import join, sep

from fabric.api import env

env.REPO_DIR = join(sep, 'opt')
env.REPO_URL = 'https://github.com/sergeesnault/deployments.git'
env.OPS_DIR = join(env.REPO_DIR, 'deployments')
env.OPS_ETC_DIR = join(env.OPS_DIR, 'ubuntu', 'etc')
# add subdomains to this list separated with a comma
# for example [env.host, domain1, domain2]
env.DOMAINS = ['www.serthe.com']
