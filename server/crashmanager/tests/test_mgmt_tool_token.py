"""Tests for add/remove tool management commands

@license:
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""
import pytest
from django.core.management import CommandError, call_command
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from crashmanager.models import Tool, User as CrashManagerUser

pytestmark = pytest.mark.django_db()

def test_add_tool_to_token_new_tool(capsys):
    """Test adding new tool to user's filter"""
    user = User.objects.create_user("testuser")
    token = Token.objects.create(user=user)

    call_command("add_tool_to_token", token.key, "newtool")

    # Check command output
    out, _ = capsys.readouterr()
    assert "Tool 'newtool' was created." in out
    assert "added to user" in out

    # Verify database state
    cm_user = CrashManagerUser.objects.get(user=user)
    assert cm_user.restricted is True
    assert cm_user.defaultToolsFilter.filter(name="newtool").exists()

def test_add_tool_to_token_existing_tool(capsys):
    """Test adding existing tool doesn't recreate it"""
    # Create tool first
    Tool.objects.create(name="existingtool")

    user = User.objects.create_user("testuser")
    token = Token.objects.create(user=user)

    call_command("add_tool_to_token", token.key, "existingtool")

    # Check command output
    out, _ = capsys.readouterr()
    assert "Tool 'existingtool' was created." not in out
    assert "added to user" in out

def test_add_tool_to_token_restricts_user(capsys):
    """Test unrestricted user becomes restricted when adding tool"""
    user = User.objects.create_user("testuser")
    cm_user = CrashManagerUser.get_or_create_restricted(user)[0]
    cm_user.restricted = False
    cm_user.save()

    token = Token.objects.create(user=user)

    call_command("add_tool_to_token", token.key, "newtool")

    # Check warning message
    out, _ = capsys.readouterr()
    assert "has been restricted for security" in out

    # Verify restriction
    cm_user.refresh_from_db()
    assert cm_user.restricted is True

def test_remove_tool_from_token_exists(capsys):
    """Test removing existing tool from filter"""
    user = User.objects.create_user("testuser")
    cm_user = CrashManagerUser.get_or_create_restricted(user)[0]
    tool = Tool.objects.create(name="oldtool")
    cm_user.defaultToolsFilter.add(tool)

    token = Token.objects.create(user=user)

    call_command("remove_tool_from_token", token.key, "oldtool")

    # Check output
    out, _ = capsys.readouterr()
    assert "removed from user" in out
    assert not cm_user.defaultToolsFilter.filter(name="oldtool").exists()

def test_remove_tool_from_token_last_tool(capsys):
    """Test warning when removing last tool"""
    user = User.objects.create_user("testuser")
    cm_user = CrashManagerUser.get_or_create_restricted(user)[0]
    tool = Tool.objects.create(name="lasttool")
    cm_user.defaultToolsFilter.add(tool)

    token = Token.objects.create(user=user)

    call_command("remove_tool_from_token", token.key, "lasttool")

    # Check warning
    out, _ = capsys.readouterr()
    assert "has no tools assigned" in out

    # Refresh from DB to get updated restriction status
    cm_user.refresh_from_db()
    assert cm_user.restricted is True

def test_remove_tool_from_token_nonexistent(capsys):
    """Test removing non-existent tool shows error"""
    user = User.objects.create_user("testuser")
    token = Token.objects.create(user=user)

    # Should return normally with error message
    call_command("remove_tool_from_token", token.key, "notexist")

    # Verify error message
    out, _ = capsys.readouterr()
    assert "Error: Tool 'notexist' is not present in the database" in out

    # Verify no changes to tools
    cm_user = CrashManagerUser.objects.get(user=user)
    assert cm_user.defaultToolsFilter.count() == 0

def test_add_tool_to_token_invalid_token(capsys):
    """Test error handling for invalid token"""
    call_command("add_tool_to_token", "invalid", "tool")
    out, _ = capsys.readouterr()
    assert "No token found for invalid" in out

def test_remove_tool_from_token_invalid_token(capsys):
    """Test error handling for invalid token"""
    call_command("remove_tool_from_token", "invalid", "tool")
    out, _ = capsys.readouterr()
    assert "No token found for invalid" in out
