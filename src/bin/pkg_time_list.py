#!/usr/bin/python

import apt
import commands
import re


def get_user_packages():

    dpkg_output = commands.getoutput('/usr/bin/dpkg --get-selections')
    pkgs = []

    for lines in dpkg_output.splitlines():

        lines = re.sub('[\\t]+', ' ', lines).strip()
        pkg, option = lines.split(' ')

        if option == "install" and not re.match(r'^lib', pkg):
            pkgs.append(pkg)

    return pkgs


def filter_auto_installed_packages(pkgs):

    apt_cache = apt.Cache()

    for pkg in pkgs[:]:

        if pkg in apt_cache:
            cache_pkg = apt_cache[pkg]

            if cache_pkg.is_auto_installed:
                pkgs.remove(pkg)


def get_time(option, pkg):

    stat_base = "stat -c '%{option}' `which {package}`"
    stat_error = 'stat: missing operand'
    stat_time = stat_base.format(option=option, package=pkg)

    pkg_time = commands.getoutput(stat_time)

    return pkg_time if not pkg_time.startswith(stat_error) else None


def get_time_from_package(pkg):

    modify = get_time('Y', pkg)
    access = get_time('X', pkg)

    return [modify, access]


def get_alternative_pkg(pkg):

    dpkg_command = "dpkg -L {0}| grep /usr/bin/"
    dpkg_command += " || dpkg -L {0}| grep /usr/sbin/"
    bin_path = '/usr/bin'
    pkg_bin = commands.getoutput(dpkg_command.format(pkg))

    for pkg_path in pkg_bin.splitlines():

        if bin_path in pkg_path:
            return pkg_path
        elif pkg in pkg_path:
            return pkg_path

    return None


def get_packages_time(pkgs):

    pkgs_time = {}

    for pkg in pkgs:

        modify, access = get_time_from_package(pkg)

        if not modify or not access:
            pkg_tmp = get_alternative_pkg(pkg)
            modify, access = get_time_from_package(pkg_tmp)

        if modify and access:
            pkgs_time[pkg] = []
            pkgs_time[pkg].append(modify)
            pkgs_time[pkg].append(access)

    return pkgs_time


def print_package_time(pkgs_time):

    for key, value in pkgs_time.iteritems():
        print "{0} : Modify {1}, Access {2}".format(key, value[0], value[1])


def get_packages_from_mark():

    dpkg_output = commands.getoutput('apt-mark showmanual')
    pkgs = []

    for pkg in dpkg_output.splitlines():

        if not re.match(r'^lib', pkg):
            pkgs.append(pkg)

    return pkgs


def main():

    user_pkgs = get_user_packages()
    print "Size of user package: {0}".format(len(user_pkgs))

    filter_auto_installed_packages(user_pkgs)
    print "Size of user package after filtering: {0}".format(len(user_pkgs))

    manual_pkgs = get_packages_from_mark()
    print "Size of user package apt-mark: {0}".format(len(manual_pkgs))

    pkgs_time = get_packages_time(manual_pkgs)
    print_package_time(pkgs_time)

    print "\nSize of dictionary: {0}".format(len(pkgs_time))

    with open('pkgs.txt', 'w') as pkgs:

        for pkg in user_pkgs:
            pkgs.write(str(pkg) + "\n")


if __name__ == "__main__":
    main()
