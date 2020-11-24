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

def get_org(github_conn, module, organization_name):
    if not HAS_GITHUB:
        module.fail_json(msg=missing_required_lib('PyGithub'),
                            exception=GITHUB_IMP_ERR)    
    try:
        org = github_conn.get_organization(organization_name)
    except github.BadCredentialsException as err:
        module.fail_json(msg="Could not authenticate to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))
    except github.UnknownObjectException as err:
        module.fail_json(
            msg="Could not find organization %s in GitHub at %s: %s" % (
                organization_name, module.params["github_url"],
                to_native(err)))
    except Exception as err:
        module.fail_json(
            msg="Could not retrieve organization %s from GitHub at %s: %s" % (
                organization_name, module.params["github_url"],
                to_native(err)),
            exception=traceback.format_exc())   
    
    return org

def get_repo(github_conn, module, owner_name, repo_name, owner_type="org"):
    if not HAS_GITHUB:
        module.fail_json(msg=missing_required_lib('PyGithub'),
                            exception=GITHUB_IMP_ERR)    
    try:
        org = get_org(github_conn, module, owner_name)
        repo = org.get_repo(name=repo_name)
    except github.BadCredentialsException as err:
        module.fail_json(msg="Could not authenticate to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))
    except github.UnknownObjectException as err:
        return None
    except Exception as err:
        module.fail_json(
            msg="Could not search for repositories in organization %s from GitHub at %s: %s" %
            (owner_name, module.params["github_url"],
             to_native(err)),
            exception=traceback.format_exc())  
    return repo

def get_team(github_conn, module, organization_name, team_name):
    if not HAS_GITHUB:
        module.fail_json(msg=missing_required_lib('PyGithub'),
                            exception=GITHUB_IMP_ERR)  
    try:
        org = get_org(github_conn, module, organization_name)
        team = org.get_team_by_slug(team_name)
    except github.BadCredentialsException as err:
        module.fail_json(msg="Could not authenticate to GitHub at %s: %s" % (
            module.params["github_url"], to_native(err)))
    except github.UnknownObjectException as err:
        module.fail_json(
            msg="Could not find team %s in organization %s. GitHub at %s: %s" % (
                team_name, organization_name, module.params["github_url"],
                to_native(err)))
    except Exception as err:
        module.fail_json(
            msg="Could not search for team %s in organization %s from GitHub at %s: %s" % (
                team_name, organization_name, module.params["github_url"],
                to_native(err)),
            exception=traceback.format_exc())
    return team