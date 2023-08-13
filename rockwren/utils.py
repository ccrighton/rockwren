import re
import ubinascii

def is_fqdn(hostname: str) -> bool:
    """
    https://en.m.wikipedia.org/wiki/Fully_qualified_domain_name
    """
    if not 1 < len(hostname) < 253:
        return False

    # Remove trailing dot
    if hostname[-1] == '.':
        hostname = hostname[0:-1]

    #  Convert to lowercase and split hostname into list of DNS labels
    labels = hostname.lower().split('.')

    #  Define pattern of DNS label
    #  Can begin and end with a number or letter only
    #  Can contain hyphens, a-z, A-Z, 0-9
    #  1 - 63 chars allowed
    fqdn = re.compile(r'^[a-z0-9]([a-z-0-9-]*[a-z0-9])?$')

    # Check that all labels match that pattern.
    return all(fqdn.match(label) for label in labels)


def pem_to_der(pem):
    pem = ''.join(pem.split('\n')[1:-2]) # remove -----BEGIN PUB KEY... lines and concatenate
    der = ubinascii.a2b_base64(pem)
    return der
