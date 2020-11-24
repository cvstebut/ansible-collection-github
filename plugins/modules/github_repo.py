#!/usr/bin/python
#
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: github_repo
short_description: Manage GitHub Repositories
description:
  - "Create and delete GitHub Repositories"
requirements:
  - "PyGithub >= 1.3.5"
options:
  name:
    description:
      - Full name of the repository
    required: true
    aliases:
      - repo
  private:
    description:
      - Set to True to create a private repository (default: False)
    required: false
    choices: [ True, False ]
    default: False
  state:
    description:
      - Whether the repository should be present or absent
    required: false
    choices: [ absent, present ]
    default: present
  user:
    description:
      - User to authenticate to GitHub as
    required: true
  organization:
    description:
      - Organization in which the repo is created
    required: true
  password:
    description:
      - Password to authenticate to GitHub with
    required: false
  token:
    description:
      - Token to authenticate to GitHub with
    required: false
  github_url:
    description:
      - Base URL of the GitHub API
    required: false
    default: https://api.github.com

author:
  - "Christian von Stebut (@cvstebut)"
'''

EXAMPLES = '''
- name:  create a new repositoriy (bearer token auth)
  cvstebut.github.github_repo:
    name: myrepository
    description: "Some description"
    private: true
    user: cvstebut
    organization: namolabs
    token: "{{ github_user_api_token }}"
'''

RETURN = '''
---
repository:
  id: repository id
  name: name of respository
  returned: when state is 'present'
  type: int
  sample: 6206
'''

import traceback

GITHUB_IMP_ERR = None
try:
    import github
    HAS_GITHUB = True
except ImportError:
    GITHUB_IMP_ERR = traceback.format_exc()
    HAS_GITHUB = False

from ansible.module_utils.basic import AnsibleModule, missing_required_lib
from ansible.module_utils._text import to_native
from ansible_collections.cvstebut.testing.plugins.module_utils import github_ansible

def _get_repo_data(repo):
    data = {
                "id": repo.id,
                "name": repo.name,
                "description": repo.description,
                "private": repo.private,
                "owner": repo.owner.login,
                "state": "present"
            }  
    return data

def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            description=dict(
                type='str', 
                required=False,
                default=""),
            private=dict(
                type='bool', 
                required=False,
                choices=(True, False),
                default=False),
            state=dict(
                type='str',
                required=False,
                choices=('absent', 'present'),
                default='present'),
            user=dict(type='str', required=True),
            organization=dict(type='str', required=True),
            password=dict(type='str', required=False, no_log=True),
            token=dict(type='str', required=False, no_log=True),
            github_url=dict(
                type='str', required=False, default="https://api.github.com")),
        mutually_exclusive=(('password', 'token'),),
        required_one_of=(("password", "token"),)
    )

    if not HAS_GITHUB:
        module.fail_json(msg=missing_required_lib('PyGithub'),
                         exception=GITHUB_IMP_ERR)

    try:
        github_conn = github.Github(
            module.params["user"],
            module.params.get("password") or module.params.get("token"),
            base_url=module.params["github_url"])
    except github.GithubException as err:
        module.fail_json(msg="Could not connect to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))


    data = {}
    repo = github_ansible.get_repo(
        github_conn, module, module.params["organization"],module.params["name"])    

    changed = False
    if repo is None and module.params["state"] == "present":
        try:
            org = github_conn.get_organization(module.params["organization"])
            repo = org.create_repo(
                name = module.params["name"], 
                private= module.params["private"],
                description= module.params["description"]
                )
        except github.GithubException as err:
            module.fail_json(
                msg="Unable to create repository %s: %s" % (
                    module.params["name"], to_native(err)))
        else:
            changed = True
            data = _get_repo_data(repo)           
    elif repo is not None and module.params["state"] == "absent":
        try:
            repo.delete()
        except github.GithubException as err:
            module.fail_json(
                msg="Unable to delete repository %s: %s" % (
                     module.params["name"], to_native(err)))
        else:
            data = {}
            changed = True
    elif repo is not None and module.params["state"] == "present":
        data = _get_repo_data(repo)

    module.exit_json(changed=changed, **data)


if __name__ == '__main__':
    main()