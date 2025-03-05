from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from crashmanager.models import Tool, User as CrashManagerUser
import sys


class Command(BaseCommand):
    help = "Removes a tool from a user's defaultToolsFilter by looking up their token."

    def add_arguments(self, parser):
        parser.add_argument("token", help="The token string from get_auth_token command")
        parser.add_argument("tool_name", help="Name of the tool to remove")

    def handle(self, *args, **options):
        token_str = options["token"]
        tool_name = options["tool_name"]

        try:
            token_obj = Token.objects.get(key=token_str)
        except Token.DoesNotExist:
            print(f"No token found for {token_str}")
            return

        crash_manager_user = CrashManagerUser.get_or_create_restricted(token_obj.user)[0]

        try:
            tool = Tool.objects.get(name=tool_name)
        except Tool.DoesNotExist:
            print(f"Error: Tool '{tool_name}' is not present in the database")
            return

        crash_manager_user.defaultToolsFilter.remove(tool)

        # Keep user restricted regardless of tool count
        if not crash_manager_user.restricted:
            crash_manager_user.restricted = True
            crash_manager_user.save()
        if not crash_manager_user.defaultToolsFilter.exists():
            print(f"User '{crash_manager_user.user.username}' has no tools assigned but remains restricted.")

        print(f"Tool '{tool_name}' removed from user '{crash_manager_user.user.username}'.")
