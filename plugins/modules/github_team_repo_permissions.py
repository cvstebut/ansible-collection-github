#!/usr/bin/python
#
# Copyright: (c) 2018, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
---
module: github_team_repo_permissions
short_description: Manage GitHub Team Permissions for existing repositories
description:
  - "Set team permissions on repositories"
requirements:
  - "PyGithub >= 1.3.5"
options:
  repository_name:
    description:
      - name of the repository (without owner)
    required: true
  state:
    description:
      - Whether the repository should be present or absent
    required: false
    choices: [ none, pull, push, admin, maintain, triage ]
    default: none
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
                "name": repo.full_name,
                "description": repo.description,
                "private": repo.private,
                "owner": repo.owner.login
            }  
    return data
def _get_permission_state(team, repo):
    permission_states = {
        'push': {'pull': True, 'triage': False, 'push': True, 'maintain': False, 'admin': False},
        'pull': {'pull': True, 'triage': False, 'push': False, 'maintain': False, 'admin': False},
        'triage': {'pull': False, 'triage': True, 'push': False, 'maintain': False, 'admin': False},
        'maintain': {'pull': False, 'triage': False, 'push': False, 'maintain': True, 'admin': False},
        'admin': {'pull': True, 'triage': False, 'push': True, 'maintain': False, 'admin': True}        
    }
    permissions = team.get_repo_permission(repo=repo)
    if permissions:
        for state in permission_states.keys():
            if permissions.raw_data == permission_states[state]:
                return state
        return 'StateNotFound'
    else:
        return 'none'

def _set_permission_state(team, repo, state):
    if state == 'none':
        team.remove_from_repos(repo=repo)
    else:
        team.set_repo_permission(repo=repo, permission=state)

def main():
    module = AnsibleModule(
        argument_spec=dict(
            repository_name=dict(type='str', required=True),
            team_name=dict(type='str', required=True),
            state=dict(
                type='str',
                required=True,
                choices=('none', 'pull', 'push', 'admin', 'maintain', 'triage')
                ),
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

    repo =  github_ansible.get_repo(github_conn, module, module.params["organization"], module.params["repository_name"])

    if repo == None:
      module.fail_json(
        msg="Repository %s does not exist in organization %s. GitHub at %s" % (
                module.params["repository_name"], module.params["organization"], module.params["github_url"])
      )

    team = github_ansible.get_team(github_conn, module, module.params["organization"], module.params["team_name"])

    changed = False
    current_state = _get_permission_state(team, repo)

    if current_state != module.params["state"]:
        _set_permission_state(team, repo, module.params["state"])
        changed = True

    module.exit_json(changed=changed, **data)

if __name__ == '__main__':
    main()