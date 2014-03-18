from rez.resources import load_package_metadata, load_package_settings
from rez.exceptions import BuildSystemError
from rez.util import which



def get_buildsys_types():
    """Returns the available build system implementations - cmake, make etc."""
    from rez.plugin_managers import build_system_plugin_manager
    return build_system_plugin_manager().get_plugins()


def get_valid_build_systems(working_dir):
    """Returns the build system classes that could build the source in given dir."""
    from rez.plugin_managers import build_system_plugin_manager

    clss = []
    for buildsys_name in get_buildsys_types():
        cls = build_system_plugin_manager().get_plugin_class(buildsys_name)
        if cls.is_valid_root(working_dir):
            clss.append(cls)
    return clss


def create_build_system(working_dir, buildsys_type=None, opts=None,
                        build_child=True, install=False, verbose=False,
                        child_build_args=[], *build_args):
    """Return a new build system that can build the source in working_dir."""
    from rez.plugin_managers import build_system_plugin_manager

    if buildsys_type:
        cls = build_system_plugin_manager().get_plugin_class(buildsys_type)
        clss = [cls]
    else:
        clss = get_valid_build_systems(working_dir)

    if clss:
        # deal with leftover tempfiles from child buildsys in working dir
        child_clss = set(x.child_build_system() for x in clss)
        clss = set(clss) - child_clss

        if len(clss) > 1:
            s = ', '.join(x.name() for x in clss)
            raise BuildSystemError(("Source could be built with one of: %s; "
                                   "Please specify a build system") % s)
        else:
            cls = iter(clss).next()
            return cls(working_dir,
                       opts=opts,
                       build_child=build_child,
                       install=install,
                       verbose=verbose,
                       child_build_args=child_build_args,
                       *build_args)
    else:
        raise BuildSystemError("No build system is associated with the path %s"
                               % working_dir)



class BuildSystem(object):
    @classmethod
    def name(cls):
        """Return the name of the build system, eg 'make'."""
        raise NotImplementedError

    def __init__(self, working_dir, opts=None, build_child=True, install=False,
                 verbose=False, child_build_args=[], *build_args):
        """Create a build system instance.

        Args:
            working_dir: Directory to build source from.
            opts: argparse.Namespace object which may contain constructor
                params, as set by our bind_cli() classmethod.
            build_child: If True, and this build system has a child system, then
                the child build step will be performed also. If False and there
                is a child system, then only the first build step should be
                performed. In this case, the system may create executable scripts,
                which when run, place the user into an environment where they
                can perform the second build step directly themselves. This is
                useful for fast iteration when build settings are not changing.
                If the build system does not have a child system, then this arg
                should be ignored.
            install: If True, install the build.
            child_build_args: Extra cli args for child build system, ignored if
                there is no child build system.
            build_args: Extra cli build arguments.
        """
        self.working_dir = working_dir
        if not self.is_valid_root(working_dir):
            raise BuildSystemError("Not a valid %s working directory: %s"
                                   % (self.name(), working_dir))

        self.metadata = load_package_metadata(working_dir)
        self.settings = load_package_settings(self.metadata)

        self.build_child = build_child
        self.install = install
        self.build_args = build_args
        self.child_build_args = child_build_args
        self.verbose = verbose

    @classmethod
    def find_executable(cls, name):
        exe = which(name)
        if not exe:
            raise BuildSystemError(("Couldn't find executable '%s' for build "
                                   "system '%s'") % (name, cls.name()))
        return exe

    @classmethod
    def is_valid_root(cls, path):
        """Return True if this build system can release the source in path."""
        raise NotImplementedError

    @classmethod
    def child_build_system(cls):
        """Returns the child build system.

        Some build systems, such as cmake, don't build the source directly.
        Instead, they build an interim set of build scripts that are then
        consumed by a second build system (such as make). You should implement
        this method if that's the case.

        Returns:
            Name of build system (corresponding to the plugin name) if this
            system has a child system, or None otherwise.
        """
        return None

    @classmethod
    def bind_cli(cls, parser):
        """Expose parameters to an argparse.ArgumentParser that are specific
        to this build system.
        """
        pass

    def build(self, context, build_path, install_path):
        """Implement this method to perform the actual build.

        Args:
            context: A ResolvedContext object that the build process must be
                executed within.
            build_path: Where to write temporary build files. May be relative
                to working_dir.
            install_path: Where to install the build, if the build is installed.

        Returns:
            - True: If the build succeeded;
            - False: If the build failed;
            - str: If there is a child system and only the first step was
              performed, and a script was made which the user can execute to
              place themselves into a build shell.
        """
        raise NotImplementedError