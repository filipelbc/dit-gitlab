#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import json
import re
import os
from datetime import timedelta, datetime

from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError

from dit.utils import (
    convert_datetimes,
    interpret_date,
)


# ========================================
# Timedelta helpers

_0_seconds = timedelta(0)
_1_day = timedelta(days=1)


_gitlab_conf_file = os.path.expanduser('~/.dit/.gitlab.conf')
_gitlab_conf_section = 'dit'


def to_gitlab_spend_string(td, dt):
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if seconds > 30:
        minutes += 1
    return "/spend %dh%dmin %s" % (hours, minutes, dt.strftime(r'%Y-%m-%d'))


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


def add_spent_time(issue, td, date):
    """
    This is a workaround because the Gitlab API does not allow specifying the
    "date".
    """
    try:
        body = to_gitlab_spend_string(td, date)
        print(body)
        issue.notes.create({'body': body})
    except Exception as e:
        print(e)


def spend_time_on(issue, task, since):
    for l in convert_datetimes(task).get('logbook', []):
        if l['in'] >= since and l['out'] is not None:
            add_spent_time(
                issue=issue,
                td=l['out'] - l['in'],
                date=l['in'].date()
            )


def get_gitlab_issue(iid, gl_project):
    try:
        return gl_project.issues.get(iid)
    except GitlabGetError:
        print("No issue found with id: %s" % iid)
        return None


# ========================================
# Main


def cli(base_path, group, subgroup, task, since):
    since = interpret_date(since)

    gl_project = get_gitlab_project(group, subgroup)
    if not gl_project:
        print("Could not choose a project to use.")
        return

    match = re.match(r'^(?P<type>i|m)(?P<id>\d+)$', task)
    if not match:
        print("Unrecognized task name pattern.")
        return

    issue = get_gitlab_issue(int(match.group('id')), gl_project)
    if issue is None:
        return

    task_fp = os.path.join(base_path, group, subgroup, task)
    with open(task_fp, 'r') as f:
        task = json.load(f)

    spend_time_on(issue, task, since)


# ========================================
# Invocation


if __name__ == "__main__":
    if len(sys.argv) != 6:
        raise Exception("ERROR: Invalid arguments: %s" % sys.argv)
    sys.argv.pop(0)

    cli(*sys.argv)
