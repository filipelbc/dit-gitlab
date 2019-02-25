#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import os
from datetime import timedelta

from gitlab import Gitlab
from gitlab.exceptions import GitlabGetError

from dit.utils import (
    convert_datetimes,
    interpret_date,
    apply_filters,
)
from dit.common import names_to_string as _
from dit.dit import Dit
from dit.exceptions import (
    ArgumentError,
    maybe_raise_unrecognized_argument,
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


def add_spent_time(issue, td, date, dry_run=False):
    """
    This is a workaround because the Gitlab API does not allow specifying the
    "date".
    """
    try:
        body = to_gitlab_spend_string(td, date)
        if not dry_run:
            print(body)
            issue.notes.create({'body': body})
        else:
            print("Dry run:", body)
    except Exception as e:
        print(e)


def spend_time_on(issue, logbook, dry_run):
    for log in logbook:
        add_spent_time(
            issue=issue,
            td=log['out'] - log['in'],
            date=log['in'].date(),
            dry_run=dry_run,
        )


def get_gitlab_issue(iid, gl_project):
    try:
        return gl_project.issues.get(iid)
    except GitlabGetError:
        print("No issue found with id: %s" % iid)
        return None


# ========================================
# Main

def get_dit():
    dit = Dit()
    dit._setup_base_path(None)
    dit._load_current()
    dit._load_previous()
    dit.index.load(dit.base_path)
    return dit


def cli(argv):
    dit = get_dit()

    dry_run = False
    filters = {}

    while len(argv) > 0 and argv[0].startswith("-"):
        opt = argv.pop(0)
        if opt in ["--dry-run"]:
            dry_run = True
        elif opt in ["--from"]:
            filters["from"] = interpret_date(argv.pop(0))
        elif opt in ["--to"]:
            filters["to"] = interpret_date(argv.pop(0))
        else:
            raise ArgumentError("No such option: %s" % opt)

    if len(argv) < 1:
        raise ArgumentError("Missing argument.")

    (group, subgroup, task) = dit._backward_parser(argv, throw=False)
    maybe_raise_unrecognized_argument(argv)
    print('Selected: %s' % _(group, subgroup, task))

    match = re.match(r'^(?P<type>i|m)(?P<id>\d+)$', task)
    if not match:
        print("Unrecognized task name pattern:", task)
        return

    data = dit._load_task_data(group, subgroup, task)
    logbook = apply_filters(convert_datetimes(data), filters).get('logbook', [])

    if not logbook:
        print("Nothing to spend.")
        return

    gl_project = get_gitlab_project(group or ".", subgroup or ".")
    if not gl_project:
        print("Could not choose a project to use.")
        return

    iid = int(match.group('id'))
    issue = get_gitlab_issue(iid, gl_project)
    if not issue:
        print("No such issue:", iid)
        return

    spend_time_on(issue, logbook, dry_run)

# ========================================
# Invocation


if __name__ == "__main__":
    sys.argv.pop(0)
    cli(sys.argv)
