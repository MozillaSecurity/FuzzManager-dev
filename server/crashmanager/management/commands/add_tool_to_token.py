from django.core.management.base import BaseCommand
from rest_framework.authtoken.models import Token
from crashmanager.models import Tool, User as CrashManagerUser


class Command(BaseCommand):
    help = "Assigns a tool to a user's defaultToolsFilter by looking up their token and ensures the user is restricted."

    def add_arguments(self, parser):
        parser.add_argument("token", help="The token string from get_auth_token command")
        parser.add_argument("tool_name", help="Name of the tool to add")

    def handle(self, *args, **options):
        token_str = options["token"]
        tool_name = options["tool_name"]

        try:
            token_obj = Token.objects.get(key=token_str)
        except Token.DoesNotExist:
            print(f"No token found for {token_str}")
            return

        crash_manager_user = CrashManagerUser.get_or_create_restricted(token_obj.user)[0]

        tool, created = Tool.objects.get_or_create(name=tool_name)
        if created:
            print(f"Tool '{tool_name}' was created.")

        # Ensure the user is restricted, so they can only access the tool being added
        if not crash_manager_user.restricted:
            crash_manager_user.restricted = True
            crash_manager_user.save()
            print(f"User '{crash_manager_user.user.username}' has been restricted for security.")

        crash_manager_user.defaultToolsFilter.add(tool)

        print(f"Tool '{tool_name}' added to user '{crash_manager_user.user.username}'.")
