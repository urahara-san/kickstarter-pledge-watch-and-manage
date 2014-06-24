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
functionality due to my curiosity for which I had to monitor the network request
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

In-built help message:

        usage: ks-watch-and-manage.py [-h] [-v] [-i {1,2,3,4,5,6,7,8,9,10}] [-nb]
                                      [-c COOKIES-FILE] [-p [PLEDGE [PLEDGE ...]]]
                                      [-pa] [-pm PLEDGE_MULTIPLE] [-fa FIXED_ADDITION]
                                      [-np]
                                      URL

        positional arguments:
          URL                   project home page URL

        optional arguments:
          -h, --help            show this help message and exit
          -i {1,2,3,4,5,6,7,8,9,10}, --interval {1,2,3,4,5,6,7,8,9,10}
                                frequency in minutes to check the project page for
                                changes (default: 5)
          -nb, --no-browser     don't open the browser when a pledge is unlocked,
                                default false
          -c COOKIES-FILE, --cookies COOKIES-FILE
                                path to the cookies file used to manage the pledge
                                (only the Netscape format is accepted)
          -p [PLEDGE [PLEDGE ...]], --pledge [PLEDGE [PLEDGE ...]]
                                pledges (numbers separated by spaces) ordered by
                                priority, highest to lowest
          -pa, --pledge-amount  pledges specified in terms of the currency amount
          -pm PLEDGE_MULTIPLE, --pledge-multiple PLEDGE_MULTIPLE
                                multiply the pledge amount with this factor (default:
                                1)
          -fa FIXED_ADDITION, --fixed-addition FIXED_ADDITION
                                add to the pledge amount (default: 0)
          -np, --no-priority    pledges don't have any priority

### Examples

#### Basic

        ./ks-watch-and-manage.py https://www.kickstarter.com/projects/12345678/some-project-i-love/

Next you will get a list of pledges avaialbe in the project and a prompt to "Select pledge levels"
wherein you can enter multiple pledges (numbers based on the list displayed) in order of priority
highest to lowest.

The script will monitor the pledges entered and open the manage plede page in the default browser.

Note: The script will keep running until the highest priority pledge is unlocked.


#### No priorities

If you want the script to continue running until all selected pledges get unlocked, you an use the
no priority option as follows:

        ./ks-watch-and-manage.py --no-priority https://www.kickstarter.com/projects/12345678/some-project-i-love/


#### Don't open the browser

If you do not want to open the browser automatically, rather just give an alert in the console do this:

        ./ks-watch-and-manage.py --no-browser https://www.kickstarter.com/projects/12345678/some-project-i-love/


#### Custom interval to check for pledge availability

Check the page for unlocked pledges once every 10 minutes. 

        ./ks-watch-and-manage.py --interval 10 https://www.kickstarter.com/projects/12345678/some-project-i-love/

#### Automatic re-pledge

First I urge you to read the disclaimer, if you haven't already done so.

To be able re-pledge automatically there are some prerequisites without which it will not be possible.

    1. Cookies from your browser, for authentication with KS, in the netscape cookie file format. Once you supply the file, the script will test to see if it can successfully login to KS. You can use the following extensions to get the required file:
      * Chrome 
      * Firefox 
      * Safari 
      * Opera

    2. You need to make a pledge to the project and make sure that the payment gateway had authentication for the maximum amount that you expect this script to make. 