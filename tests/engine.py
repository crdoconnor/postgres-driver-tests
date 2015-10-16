from hitchserve import ServiceBundle
from os import path, system, chdir
from subprocess import check_call, PIPE
import hitchpostgres
import hitchtest
import hitchcli


# Get directory above this file
PROJECT_DIRECTORY = path.abspath(path.join(path.dirname(__file__), '..'))


class ExecutionEngine(hitchtest.ExecutionEngine):
    """Python engine for running tests."""

    def set_up(self):
        """Set up your applications and the test environment."""

        # COMPILE YOUR C++ APPLICATION HERE
        #check_call(["make"])

        postgres_package = hitchpostgres.PostgresPackage(
            version=self.preconditions["postgres_version"],
        )
        postgres_package.build()

        self.services = ServiceBundle(
            project_directory=PROJECT_DIRECTORY,
            startup_timeout=float(self.settings["startup_timeout"]),
            shutdown_timeout=float(self.settings["shutdown_timeout"]),
        )

        # Create postgres user and database
        postgres_user = hitchpostgres.PostgresUser("example", "password")

        self.services['Postgres'] = hitchpostgres.PostgresService(
            postgres_package=postgres_package,
            users=[postgres_user, ],
            databases=[hitchpostgres.PostgresDatabase("example", postgres_user), ]
        )

        self.services.startup(interactive=False)

        self.cli_steps = hitchcli.CommandLineStepLibrary(default_timeout=90)

        self.cd = self.cli_steps.cd
        self.run = self.cli_steps.run
        self.expect = self.cli_steps.expect
        self.send_control = self.cli_steps.send_control
        self.send_line = self.cli_steps.send_line
        self.exit_with_any_code = self.cli_steps.exit_with_any_code
        self.exit = self.cli_steps.exit

        chdir(PROJECT_DIRECTORY)

    def run_sql(self, sql=None, database=None):
        self.services['Postgres'].databases[0].psql(sql)

    def pause(self, message=None):
        """Pause test and launch IPython"""
        if hasattr(self, 'services'):
            self.services.start_interactive_mode()
        self.ipython(message)
        if hasattr(self, 'services'):
            self.services.stop_interactive_mode()

    def time_travel(self, days=""):
        """Move Postgres forward in time"""
        self.services.time_travel(days=int(days))

    def connect_to_kernel(self, service_name):
        """Connect to IPython kernel embedded in service_name."""
        self.services.connect_to_ipykernel(service_name)

    def on_failure(self):
        """Runs if there is a test failure"""
        if not self.settings['quiet']:
            if self.settings.get("pause_on_failure", False):
                self.pause(message=self.stacktrace.to_template())

    def on_success(self):
        """Runs when a test successfully passes"""
        if self.settings.get("pause_on_success", False):
            self.pause(message="SUCCESS")

    def tear_down(self):
        """Run at the end of all tests."""
        if hasattr(self, 'services'):
            self.services.shutdown()
