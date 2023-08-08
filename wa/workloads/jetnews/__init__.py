from wa import Workload


class JetNewsScrollArticle(Workload):
    name = "jetnewsScrollArticle"
    description = "Run the JetNews ScrollArticleTest"
    package_names = ["com.example.jetnews", "com.arm.benchmark"]

    def setup(self, context):
        super(JetNewsScrollArticle, self).setup(context)
        for package in self.package_names:
            self.target.execute(f"am force-stop {package}")

    def run(self, context):
        super(JetNewsScrollArticle, self).run(context)
        self.target.execute((
            "am instrument -w "
            "-e class com.arm.test.ScrollArticleTest "
            "com.arm.benchmark/androidx.test.runner.AndroidJUnitRunner"
        ))

    def teardown(self, context):
        super(JetNewsScrollArticle, self).teardown(context)
        for package in self.package_names:
            self.target.execute(f"am force-stop {package}")
