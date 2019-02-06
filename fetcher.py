#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import re
import os
from datetime import timedelta

from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError

# ========================================
# Timedelta helpers

_0_seconds = timedelta(0)


_gitlab_conf_file = os.path.expanduser('~/.dit/.gitlab.conf')
_gitlab_conf_section = 'dit'


def timedelta_to_str(td):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return "%02d:%02d" % (td.days + hours, minutes)


def str_to_timedelta(string):
    if string:
        hours, minutes = map(int, string.split(':'))
        return timedelta(hours=hours, minutes=minutes)
    return timedelta()

# ========================================
# Functionality


def get_group_project_map():
    return {
    }


def get_project_for_group(group, subgroup):
    gp_map = get_group_project_map()

    if group not in gp_map:
        return None
    if subgroup not in gp_map[group]:
        return None

    return gp_map[group][subgroup]


def get_gitlab_project(group, subgroup):
    project = get_project_for_group(group, subgroup)
    if project is None:
        return None

    gl = Gitlab.from_config(_gitlab_conf_section, [_gitlab_conf_file])
    return gl.projects.get(project)


def get_issue_estimate(issue):
    # FIXME
    return None


def issue_to_task_data(iid, gl_project):
    try:
        issue = gl_project.issues.get(iid)
    except GitlabGetError:
        print("No issue found with id: %s" % iid)
        return None

    data = {
        'title': issue.title,
        'properties': {
            'issues': str(iid),
            'status': issue.state,
        }
    }

    estimate = get_issue_estimate(issue)
    if estimate:
        data['properties']['estimate'] = estimate

    return data


def mergerequest_to_task_data(mid, gl_project):
    mr = gl_project.mergerequests.get(mid)

    data = {
        'title': mr.title,
        'properties': {'merge-request': str(mid)}
    }

    closes_issues = mr.closes_issues()

    data['properties']['issues'] = [str(issue.iid) for issue in closes_issues]

    estimate = sum([
        str_to_timedelta(get_issue_estimate(issue))
        for issue in closes_issues
    ], _0_seconds)
    if estimate > _0_seconds:
        data['properties']['estimate'] = timedelta_to_str(estimate)

    return data

# ========================================
# Main


def cli(base_path, group, subgroup, task):
    gl_project = get_gitlab_project(group, subgroup)
    if not gl_project:
        print("Could not choose a project to use.")
        return

    match = re.match(r'^(?P<type>i|m)(?P<id>\d+)$', task)
    if not match:
        print("Unrecognized task name pattern.")
        return

    if match.group('type') == 'i':
        data = issue_to_task_data(int(match.group('id')), gl_project)

    else:  # match.group('type') == 'm'
        data = mergerequest_to_task_data(int(match.group('id')), gl_project)

    if not data:
        print("Could not fetch any data.")
        return

    # save data
    task_fp = os.path.join(base_path, group, subgroup, task) + '.json'
    with open(task_fp, 'w') as f:
        f.write(json.dumps(data))

# ========================================
# Invocation


if __name__ == "__main__":
    if len(sys.argv) != 5:
        raise Exception("ERROR: Invalid arguments: %s" % sys.argv)
    sys.argv.pop(0)

    cli(*sys.argv)
