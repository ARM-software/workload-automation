from wa import Workload

class JetNews(Workload):
    name = "jetnews"
    description = "Run the JetNews basic tests"
    package_names = ["com.example.jetnews", "com.arm.benchmark"]

    def setup(self, context):
        super(JetNews, self).setup(context)
        for package in self.package_names:
            self.target.execute(f"am force-stop {package}")

    def run(self, context):
        super(JetNews, self).run(context)

        # Run the first set of basic tests:
        tests = ["ScrollArticleTest",
                 "ScrollArticleSlowlyTest",
                 "UserSimulationTest"]

        # Invoke each test one after the other.
        for test in tests:
            self.target.execute(
                "am instrument -w "
                "-e class com.arm.test." + test + " "
                "com.arm.benchmark/androidx.test.runner.AndroidJUnitRunner"
            )

    def teardown(self, context):
        super(JetNews, self).teardown(context)
        for package in self.package_names:
            self.target.execute(f"am force-stop {package}")
