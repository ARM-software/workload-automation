from wlauto import AndroidDevice


class MeizuMX6(AndroidDevice):

    name = 'meizumx6'

    @property
    def is_rooted(self):
        # "su" executable on a rooted Meizu MX6 is targeted
        # specifically towards Android application and cannot
        # be used to execute a command line shell. This makes it
        # "broken" from WA prespective.
        return False
