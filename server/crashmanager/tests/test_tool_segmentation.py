"""Tests for tool segmentation feature

@license:
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import json
import pytest
from django.contrib.auth.models import User, Permission
from rest_framework import status
from django.contrib.contenttypes.models import ContentType

from crashmanager.models import Tool, User as CrashManagerUser, Client
from covmanager.models import Repository

pytestmark = pytest.mark.django_db()

@pytest.fixture
def tools():
    return [
        Tool.objects.create(name="tool1"),
        Tool.objects.create(name="tool2"),
        Tool.objects.create(name="tool3"),
    ]

def test_restricted_user_crash_report_authorized_tool(user_restricted, api_client, cm, tools):
    """Test restricted user can report crash with authorized tool"""
    cm.create_toolfilter("tool1", user=user_restricted.username)

    # Create testcase first
    testcase = cm.create_testcase("test.txt", quality=0)

    crash_data = cm.create_crash(
        tool=tools[0].name,
        shortSignature="test_crash",
        crashdata="test_data",
        product="test_product",
        product_version="1.0",
        platform="linux",
        testcase=testcase
    )

    data = {
        "rawStdout": crash_data.rawStdout,
        "rawStderr": crash_data.rawStderr,
        "rawCrashData": crash_data.rawCrashData,
        "testcase": "test.txt",
        "tool": "tool1",
        "platform": "x86_64",
        "product": "test_product",
        "os": "linux",
        "client": "testclient",
        "testcase_ext": "txt",
        "testcase_isbinary": False,
        "testcase_quality": 0,
        "product_version": "1.0",
    }

    response = api_client.post("/crashmanager/rest/crashes/", data)
    assert response.status_code == status.HTTP_201_CREATED

def test_restricted_user_crash_report_unauthorized_tool(user_restricted, api_client, cm, tools):
    """Test restricted user cannot report crash with unauthorized tool"""
    cm.create_toolfilter("tool1", user=user_restricted.username)

    # Add testcase creation
    testcase = cm.create_testcase("test.txt", quality=0)

    crash_data = cm.create_crash(
        tool=tools[1].name,
        shortSignature="test_crash",
        crashdata="test_data",
        product="test_product",
        product_version="1.0",
        platform="linux",
        testcase=testcase
    )

    data = {
        "tool": "tool2",
        "platform": "x86_64",
        "product": "mozilla-central",
        "os": "linux",
        "client": "testclient",
        "testcase_ext": "txt",
        "testcase_isbinary": False,
        "testcase_quality": 0,
        "rawStdout": crash_data.rawStdout,
        "rawStderr": crash_data.rawStderr,
        "rawCrashData": crash_data.rawCrashData,
        "testcase": crash_data.testcase.test,
    }

    response = api_client.post("/crashmanager/rest/crashes/", data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "You don't have permission to use tool: tool2" in response.data["message"]

def test_restricted_user_coverage_multiple_tools(user_restricted, api_client, cm, tools):
    # Add base view permission
    view_perm = Permission.objects.get(codename='view_covmanager')
    user_restricted.user_permissions.add(view_perm)

    # Add collection submission permission
    submit_perm = Permission.objects.get(codename='covmanager_submit_collection')
    user_restricted.user_permissions.add(submit_perm)

    # Then create toolfilter and test as before
    cm.create_toolfilter("tool1", user=user_restricted.username)

    coverage_data = {
        "repository": "testrepo",
        "revision": "abc123",
        "branch": "master",
        "tools": "tool1,tool2",
        "coverage": json.dumps({
            "linesTotal": 1000,
            "linesCovered": 500,
            "coveragePercent": 50.0
        }),
        "client": "testclient"
    }

    response = api_client.post("/covmanager/rest/collections/", coverage_data)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "You don't have permission to use the following tools" in response.data["message"]

def test_unrestricted_user_crash_report_any_tool(user_normal, api_client, cm, tools):
    """Test unrestricted user can report crash with any tool"""
    # Add required permissions
    view_perm = Permission.objects.get(codename='view_crashmanager')
    report_perm = Permission.objects.get(codename='crashmanager_report_crashes')
    user_normal.user_permissions.add(view_perm, report_perm)

    # Add testcase creation
    testcase = cm.create_testcase("test.txt", quality=0)

    crash_data = cm.create_crash(
        tool=tools[2].name,
        shortSignature="test_crash",
        crashdata="test_data",
        product="test_product",
        product_version="1.0",
        platform="linux",
        testcase=testcase
    )

    data = {
        "rawStdout": crash_data.rawStdout,
        "rawStderr": crash_data.rawStderr,
        "rawCrashData": crash_data.rawCrashData,
        "testcase": "test.txt",
        "tool": "tool3",
        "platform": "x86_64",
        "product": "test_product",
        "os": "linux",
        "client": "testclient",
        "testcase_ext": "txt",
        "testcase_isbinary": False,
        "testcase_quality": 0,
        "product_version": "1.0",
    }

    response = api_client.post("/crashmanager/rest/crashes/", data)
    assert response.status_code == status.HTTP_201_CREATED

def test_restricted_user_coverage_single_authorized_tool(user_restricted, api_client, cm, tools):
    # Add required permissions
    view_perm = Permission.objects.get(codename='view_covmanager')
    submit_perm = Permission.objects.get(codename='covmanager_submit_collection')
    user_restricted.user_permissions.add(view_perm, submit_perm)

    # Create toolfilter for authorized tool
    cm.create_toolfilter("tool1", user=user_restricted.username)

    # Create required client
    Client.objects.create(name="testclient")

    # Create required repository
    Repository.objects.create(name="testrepo", classname="git")

    coverage_data = {
        "repository": "testrepo",
        "revision": "abc123",
        "branch": "master",
        "tools": "tool1",
        "platform": "x86_64",
        "os": "linux",
        "description": "testdesc",
        "coverage": json.dumps({
            "linesTotal": 1000,
            "linesCovered": 500,
            "coveragePercent": 50.0
        }),
        "client": "testclient"
    }

    response = api_client.post("/covmanager/rest/collections/", coverage_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

def test_restricted_user_coverage_single_unauthorized_tool(user_restricted, api_client, cm, tools):
    # Add required permissions
    view_perm = Permission.objects.get(codename='view_covmanager')
    submit_perm = Permission.objects.get(codename='covmanager_submit_collection')
    user_restricted.user_permissions.add(view_perm, submit_perm)

    coverage_data = {
        "repository": "testrepo",
        "revision": "abc123",
        "branch": "master",
        "tools": "tool1",
        "platform": "x86_64",
        "os": "linux",
        "coverage": json.dumps({
            "linesTotal": 1000,
            "linesCovered": 500,
            "coveragePercent": 50.0
        }),
        "client": "testclient"
    }

    response = api_client.post("/covmanager/rest/collections/", coverage_data, format='json')
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "No tools assigned to user" in response.data["message"]

def test_unrestricted_user_coverage_single_tool(user_normal, api_client, cm, tools):
    # Add required permissions
    view_perm = Permission.objects.get(codename='view_covmanager')
    submit_perm = Permission.objects.get(codename='covmanager_submit_collection')
    user_normal.user_permissions.add(view_perm, submit_perm)

    # Create required client
    Client.objects.create(name="testclient")

    Repository.objects.create(name="testrepo", classname="git")

    coverage_data = {
        "repository": "testrepo",
        "revision": "abc123",
        "branch": "master",
        "tools": "tool2",
        "platform": "x86_64",
        "os": "linux",
        "description": "testdesc",
        "coverage": json.dumps({
            "linesTotal": 1000,
            "linesCovered": 500,
            "coveragePercent": 50.0
        }),
        "client": "testclient"
    }

    response = api_client.post("/covmanager/rest/collections/", coverage_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED

def test_unrestricted_user_coverage_multiple_tools(user_normal, api_client, cm, tools):
    # Add required permissions
    view_perm = Permission.objects.get(codename='view_covmanager')
    submit_perm = Permission.objects.get(codename='covmanager_submit_collection')
    user_normal.user_permissions.add(view_perm, submit_perm)

    # Create required client
    Client.objects.create(name="testclient")

    Repository.objects.create(name="testrepo", classname="git")

    coverage_data = {
        "repository": "testrepo",
        "revision": "abc123",
        "branch": "master",
        "tools": "tool1,tool3",
        "platform": "x86_64",
        "os": "linux",
        "description": "testdesc",
        "coverage": json.dumps({
            "linesTotal": 1000,
            "linesCovered": 500,
            "coveragePercent": 50.0
        }),
        "client": "testclient"
    }

    response = api_client.post("/covmanager/rest/collections/", coverage_data, format='json')
    assert response.status_code == status.HTTP_201_CREATED
