Kickstarter pledge watch and manage
===================================

This Python program notifies you when a locked Kickstarter pledge level
becomes available and optionally, manage your pledge.

Disclaimer
----------

I, in line with the original author of this script, believe that this
script does not violate the Kickstarter terms of service (TOS) listed
here https://www.kickstarter.com/terms-of-use :

    Additionally, you shall not: (i) take any action that imposes or may
    impose (as determined by the Company in its sole discretion) an
    unreasonable or disproportionately large load on the Company's or its
    third-party providers' infrastructure; (ii) interfere or attempt to
    interfere with the proper working of the Service or any activities
    conducted on the Service; (iii) bypass any measures the Company may use to
    prevent or restrict access to the Service (or other accounts, computer
    systems, or networks connected to the Service); (iv) run Maillist,
    Listserv, or any form of auto-responder or "spam" on the Service; or (v)
    use manual or automated software, devices, or other processes to "crawl"
    or "spider" any page of the Site.

As long as this script is run no more frequently than once a minute, it will
not "impose ... an unreasonable or disproportionately large load on the
Company's or its third-party providers' infrastructure".  Secondly, this tool
does not "crawl" or "spider" the Kickstarter web site or any page. Wikipedia
defines crawling as "an Internet bot that systematically browses the World
Wide Web, typically for the purpose of Web indexing." The script does not
index any pages, it just scrapes a single page. Furthermore Wikipedia states
that "Sites use Web crawling or spidering software to update their web content
or indexes of others sites' web content. Web crawlers can copy all the pages
they visit for later processing" This script does not store any data for later
processing, rather it relays real-time information directly to the user.

However the other functionality of the script, namely managing the plege, I
feel may violate the TOS:

    You shall not directly or indirectly: (i) decipher, decompile, disassemble,
    reverse engineer, or otherwise attempt to derive any source code or underlying
    ideas or algorithms of any part of the Service, except to the extent
    applicable laws specifically prohibit such restriction; (ii) modify, translate,
    or otherwise create derivative works of any part of the Service; or
    (iii) copy, rent, lease, distribute, or otherwise transfer any of the rights
    that you receive hereunder.

After coming across the original script I tried to extend it's
functionality due to my curiosity which forced me to monitor the network request
created by the manage pledge page. The monitoring would probably fall under
deciphering the system so use this functionality at your own risk. KS clearly
states that they:

    Kickstarter reserves the right to cancel a pledge at any time and for any
    reason.

    The Company may terminate your access to the Service, without cause or
    notice, which may result in the forfeiture and destruction of all information
    associated with your account. If you wish to terminate your account, you may
    do so by following the instructions on the Site. Any fees paid to the
    Company are non-refundable. All provisions of the Terms of Use that by their
    nature should survive termination shall survive termination, including,
    without limitation, ownership provisions, warranty disclaimers, indemnity,
    and limitations of liability.

Again, for the sake of clarity, I state that the automated pledge selection
functionality may violate the TOS.

Usage guidelines
----------------

TODO
