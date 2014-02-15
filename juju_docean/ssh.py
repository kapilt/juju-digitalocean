import subprocess
import logging

log = logging.getLogger('juju.docean')


def check_ssh(host, user="root"):
    cmd = ["/usr/bin/ssh", "%s@%s" % (user, host), "ls"]
    process = subprocess.Popen(
        args=cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output, err = process.communicate()
    retcode = process.poll()

    if retcode:
        raise subprocess.CalledProcessError(retcode, cmd, output + (err or ''))
    return True


def update_instance(host, user="root"):
    base = ["/usr/bin/ssh", "%s@%s" % (user, host)]
    subprocess.check_output(
        base + ["apt-get", "update"], stderr=subprocess.STDOUT)
# Don't really need to update the image, just the package lists.
#    subprocess.check_output(base + [
#        'DEBIAN_FRONTEND=noninteractive',
#        'APT_LISTCHANGES_FRONTEND=none',
#        "apt-get", "upgrade"])
