#!/usr/bin/env python

# Copyright 2013, Timur Tabi
# Copyright 2014, Prakhar Birla
# Copyright 2014, github.com/urahara-san
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# This software is provided by the copyright holders and contributors "as is"
# and any express or implied warranties, including, but not limited to, the
# implied warranties of merchantability and fitness for a particular purpose
# are disclaimed. In no event shall the copyright holder or contributors be
# liable for any direct, indirect, incidental, special, exemplary, or
# consequential damages (including, but not limited to, procurement of
# substitute goods or services; loss of use, data, or profits; or business
# interruption) however caused and on any theory of liability, whether in
# contract, strict liability, or tort (including negligence or otherwise)
# arising in any way out of the use of this software, even if advised of
# the possibility of such damage.

import sys
import os
import time
import urllib
import urllib2
import cookielib
import HTMLParser
import json
import webbrowser
import argparse
import pprint
import logging
import getpass

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("main")

# Instead of parsing the HTML, we will parse some Javascript variables
# embedded in the page. The values contained in them are mostly json
# strings. These variables get a lot of data regarding the project,
# assumably KS uses this to partially render the page in the browser.
#
# Along with the project information, this also contains the logged in
# user info. Unfortunately the amazon pledge authorization is not
# included, hence it's impossible to find out the limit of raising the
# pledges. Due to this I recommend that you pledge for a higher amount
# and let the script handle to rest.
#
# The 'rewards' dictionary uses the reward value as a key, and
# (status, remaining) as the value.
class KickstarterHTMLParser(HTMLParser.HTMLParser):
    def __init__(self, url):
        HTMLParser.HTMLParser.__init__(self)
        self.in_form_block = False    # True == we're inside an <form class='...'> block
        self.in_script_block = False # True == we're inside a <script> block
        self.in_login_block = False # True == we're inside the login form div
        self.must_enter_password = False
        self.url = url
        self.logger = logging.getLogger("parser")

    def process(self, page = 'new') :
        while True:
            try:
                url = self.url + '/' + page
                self.logger.debug('Opening URL- ' + url)
                f = urllib2.urlopen(url)
                break
            except urllib2.HTTPError as e:
                self.logger.error('HTTP Error', exc_info=True)
            except urllib2.URLError as e:
                self.logger.error('URL Error', exc_info=True)
                print 'URL Error', e
            except Exception as e:
                self.logger.error('Error', exc_info=True)

            self.logger.info('Due to error, retrying in 1 minute')
            time.sleep(60)

        html = unicode(f.read(), 'utf-8')
        f.close()
        self.logger.debug('Fetched URL successfully')

        self.rewards = []
        self.form_hidden_inputs = {}
        self.json_variables = {}


        self.logger.debug('Parsing fetched content')
        self.feed(html)   # feed() starts the HTMLParser parsing
        text_file = open("http_reponse.html", "w")
        text_file.write(html.encode('utf-8'))
        text_file.close()
        self.logger.debug('Completed parsing content')

        # if the json variable current_project was loaded, then
        # move information contained in the respective fields
        if 'current_project' in self.json_variables:
            for reward in self.json_variables['current_project']['rewards']:
                if reward['id'] == 0: continue
                if True or 'limit' in reward: # only put limited rewards
                    reward['remaining'] = reward['remaining'] if 'remaining' in reward else 1000
                    self.rewards.append((
                        float(reward['minimum']),
                        reward['remaining'],
                        str(reward['remaining']) + ' of ' + str(reward['limit']) if 'limit' in reward else 'Unlimited',
                        reward['id'],
                        reward['reward'].replace("\r\n",' '),
                        float(reward['shipping_amount']) if reward['shipping_applicable'] else 0.0))
        
        self.logged_in = True if 'current_user' in self.json_variables else False

        self.pre_pledged = {'amount':self.json_variables['current_checkout']['amount'],
        'id':self.json_variables['current_checkout']['reward']['id']} \
        if ('current_checkout' in self.json_variables and
        self.json_variables['current_checkout']['amount'] > 0) else {'amount':0,'id':0}

        # pprint.pprint(self.rewards)
        # pprint.pprint(self.pre_pledged)
        
        return self.rewards

    def handle_starttag(self, tag, attributes):
        global status

        attrs = dict(attributes)

        if tag == 'script' and len(attrs) == 0:
            self.in_script_block = True
            return

        if tag == 'div' and 'id' in attrs and attrs['id'] == 'login-signup':
            self.in_form_block = True
            self.must_enter_password = True
            self.logger.debug("Must enter password")
            return

        # TODO instead of this, just read the meta tags
        # and disengage the parsing when the body tag is reached

        # It turns out that we only care about tags that have a 'class' attribute
        if not 'class' in attrs:
            return

        if tag == 'form' and attrs['class'] == 'manage_pledge':
            self.in_form_block = True
            return

        if self.in_form_block and tag == 'input' and attrs['class'] == 'hidden':
            self.form_hidden_inputs[attrs['name']] = attrs['value']
            return

    def handle_endtag(self, tag):
        if tag == 'form':
            self.in_form_block = False
            self.in_login_block = False

        if tag == 'script':
            self.in_script_block = False

    def handle_data(self, data):
        if self.in_script_block:
            # find the variable we are interested in
            start = data.find("current_");
            # only consider if it's in the beinning
            if start > 0 and start < 30:
                # print data
                data = data[start:-8] # trim the last 8 chars
                each_line = data.split('\n') #process each line seperately
                for line in each_line:
                    start = line.find("current_") # find the variable we are interested in
                    if start < 0:
                        continue #process the next line if its not found
                    
                    variable_name =  line[start:line.find('=')-1] # extract the variable name

                    # extract the raw json and do a html decode, and some weird bug python unscape
                    raw_json = self.unescape(line[line.find('= ')+2:line.rfind(';')]).replace('\\"','\"')
                    
                    if (raw_json[0] == '"' and raw_json[-1] == '"'): # trim quotes, if present and decode as json
                        raw_json = raw_json[1:-1]
                        result = json.loads(raw_json) # json decode the string.. i.e. make it an object
                    else:
                        if (raw_json[0] == '\'' and raw_json[-1] == '\''): # trim quotes, if present
                            raw_json = raw_json[1:-1]
                        result = raw_json # consider the variable as a string

                    self.json_variables[variable_name] = result # save the result
                    # print "---"
                    # print variable_name
                    # print "==="
                    # print raw_json
                    # print "---"
                    
                    # print raw_json
                    # pprint.pprint(self.json_variables[variable_name])
                

    # def parse_only_digits(self, data):
    #     amount = data.encode('ascii','ignore')
    #     nondigits = amount.translate(None, '0123456789.')
    #     return amount.translate(None, nondigits)

    def result(self):
        return self.rewards

class KickstarterPledgeManage:
    def __init__(self, cookies_file, parser, url, login = None, password = None):
        self.logger = logging.getLogger("manage")
        if cookies_file:
            self.logger.debug('Using the cookie file')
            self.cookie_jar = cookielib.MozillaCookieJar(cookies_file)
            self.cookie_jar.load()
        else:
            self.logger.debug('Using an empty cookie jar')
            self.cookie_jar = cookielib.CookieJar()
        # self.cookie_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookie_jar))
        self.cookie_opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0),
            urllib2.HTTPSHandler(debuglevel=0),
            urllib2.HTTPCookieProcessor(self.cookie_jar)
        )
        self.parser = parser
        self.proxy_handler = urllib2.ProxyHandler({})
        self.blank_opener = urllib2.build_opener(self.proxy_handler)
        self.url = url
        self.password = password
        self.login = login

    def run_test(self):
        self.logger.debug('Starting cookie test')
        self.engage_cookie() # use the cookies
        self.parser.process() # fetch the page
        result = self.parser.logged_in
        self.logger.debug('Completed cookie test')
        self.disengage_cookie()

        # pprint.pprint(self.parser.json_variables, indent = 2)
        return result

    def change_pledge(self, id, multiply_ = 1, add_ = 0):
        self.logger.debug('Changing pledge')
        self.engage_cookie() # use the cookies
        rewards = self.parser.process('edit') # fetch the page

        submit_data = self.parser.form_hidden_inputs
        pprint.pprint(self.parser)

        if self.parser.must_enter_password:
            submit_data['user_session[password]'] = self.password
            submit_data['user_session[email]'] = self.login
            submit_data['utf8'] = '' # urllib.encode doesn't support encoding of utf8 characters
            #pprint.pprint(submit_data)
            #pprint.pprint(self.login)
            #pprint.pprint(self.password)
            data = urllib.urlencode(submit_data)
            f = urllib2.urlopen(url='https://www.kickstarter.com/user_sessions', data=data)
            html = unicode(f.read(), 'utf-8')
            f.close()
            #text_file = open("login_reponse.html", "w")
            #text_file.write(html.encode('utf-8'))
            #text_file.close()
            rewards = self.parser.process('edit')
            self.cookie_jar.save()

        self.logger.info('Creating re-pledge request')
        
        submit_data['utf8'] = '' # urllib.encode doesn't support encoding of utf8 characters
        submit_data['backing[amount]'] = s[0] * multiply_
        if submit_data['backing[domestic]'] == '0':
            submit_data['backing[amount]'] += s[5] #international shipping
        submit_data['backing[amount]'] += s[0] * add_
        submit_data['backing[backer_reward_id]'] = id
        data = urllib.urlencode(submit_data)

        result = urllib2.urlopen(url=self.url, data=data).read()

        #TODO: verify whether the re-pledge was a success

        self.disengage_cookie()

    def engage_cookie(self):
        urllib2.install_opener(self.cookie_opener)

    def disengage_cookie(self):
        urllib2.install_opener(self.blank_opener)

    def engage_login_opener(self):
        urllib2.install_opener(self.login_opener)


def pledge_menu(rewards):
    import re

    count = len(rewards)

    if count == 1:
        return rewards[0]

    for i in xrange(count):
        print '%u. $%u %s' % (i + 1, rewards[i][0], rewards[i][4][:70])
        print '\t\t %s' % (rewards[i][2])

    while True:
        try:
            ans = raw_input('\nSelect pledge levels: ')
            numbers = map(int, ans.split())
            return [rewards[i - 1] for i in numbers]
        except (IndexError, NameError, SyntaxError):
            continue

parser = argparse.ArgumentParser(
    description="This script notifies you by opening the manage pledge page" +
    " in the browser when a locked Kickstarter  pledge level becomes available" +
    " or optionally, change your pledge automatically.")
parser.add_argument("url", help="project home page URL",
    metavar="URL")
# parser.add_argument("-v", "--verbose", action="store_true",
#     help="ask questions to set up the options")
parser.add_argument("-i", "--interval", type=int,
    choices=xrange(1, 11), default=5,
    help="frequency in minutes to check the project page for changes" +
    " (default: %(default)s)")
parser.add_argument("-nb", "--no-browser", action="store_true",
    help="don't open the browser when a pledge is unlocked, default false")
parser.add_argument("-c", "--cookies", type=file,
    metavar="COOKIES-FILE",
    help="path to the cookies file used to manage the pledge" +
    " (only the Netscape format is accepted)")
parser.add_argument("-l", "--login", type=str,
    help="login into Kickstarter using the account username and password")
parser.add_argument("-pwd", "--password", type=str,
    help="login into Kickstarter using the account username and password")
# parser.add_argument("-d", "--destroy", action="store_true",
#     help="destroy (/cancel) pledge if the required pledge(s) couldn't be" +
#     " selected (requires cookies)")
# parser.add_argument("-dt", "--destroy-threshhold", type=int,
#     choices=xrange(1, 11), default=5,
#     help="time (in minutes) to project completion to destroy (cancel) the pledge" +
#     " (default: %(default)s) (requires cookies)")
parser.add_argument("-p", "--pledge", nargs="*", type=int,
    help="pledges (numbers separated by spaces) ordered" +
    " by priority, highest to lowest")
parser.add_argument("-pa", "--pledge-amount", action='store_true',
    help="pledges specified in terms of the currency amount")
parser.add_argument("-pm", "--pledge-multiple", type=int, default=1,
    help="multiply the pledge amount with this factor (default: 1)")
parser.add_argument("-fa", "--fixed-addition", type=int, default=0,
    help="add to the pledge amount (default: 0)")
parser.add_argument("-np", "--no-priority", action="store_true",
    help="pledges don't have any priority")
args = parser.parse_args()

logger.debug("Parsed args - " + pprint.pformat(args))

# Generate the URL
url = args.url.split('?', 1)[0]  # drop the stuff after the ?
base_url = url
url += '/pledge' # we want the pledge-editing page
pledges = None   # The pledge amounts on the command line
ids = None       # A list of IDs of the pledge levels
selected = None  # A list of selected pledge levels
rewards = None   # A list of valid reward levels
use_cookies = False
use_login = False

stats = None   # A list of the initial statuses of the selected pledge level
priority = None
test_passed = True

ks = KickstarterHTMLParser(url)

if args.cookies:
    # need to test the credentials
    use_cookies = True
    logger.info('Testing supplied credentials (cookies)')
    pledge_manage = KickstarterPledgeManage(args.cookies.name, ks, url)
    if not pledge_manage.run_test():
        logger.info('Unable to login to Kickstarter using the cookies provided')
        sys.exit(0)
    else:
        logger.info('Successfully logged into Kickstarter using cookies')

if args.login:
    use_cookies = True
    password = getpass.getpass('Enter account password :') if not args.password else args.password
    login = args.login
    logger.info('Testing supplied credentials (username)')
    logger.info(login)
    logger.info(password)
    if not args.cookies:
        pledge_manage = KickstarterPledgeManage(None, ks, url, login=login, password=password)
    else:
        pledge_manage = KickstarterPledgeManage(args.cookies.name, ks, url, login=login, password=password)


if args.pledge_amount:
    logger.debug('Pledges are given in amount')
    pledges = args.pledge
else:
    logger.debug('Pledges are given by ID')
    ids = args.pledge

while True:

    rewards = ks.process()

    if not rewards:
        logger.info('No limited rewards for this Kickstarter')
        sys.exit(0)

    if ids:
        selected = [r for r in rewards if r[3] in ids]
    else:
        if pledges:
            selected = [r for r in rewards if r[0] in pledges]
            pledges = None
        else:
            # If a pledge amount was not specified on the command-line, then prompt
            # the user with a menu
            selected = pledge_menu(rewards)

        # pprint.pprint(selected)
        ids = [s[3] for s in selected]
        stats = [s[1] for s in selected]
        priority = range(0,len(ids))
        pledge_priority_reached = len(ids) + 1

    for stat, s, id, current_priority in zip(stats, selected, ids, priority):

        if s[1] > 0 or s[2] == 'Unlimited' and current_priority < pledge_priority_reached:

            if use_cookies:
                pledge_manage.change_pledge(id, args.pledge_multiple, args.fixed_addition)
                print 'Re-pledged!!!'
            else :
                if args.no_browser:
                    print 'Alert!!! Monitored pledge is unlocked: ', s[4]
                else:
                    webbrowser.open_new_tab(url)
                    time.sleep(10)   # Give the web browser time to opens

            pledge_priority_reached = current_priority
            
            # ids = [x for x in ids if x != id]   # Remove the pledge we just found
            # priority.pop()

            del ids[current_priority:len(ids)] # Remove the pledge we just found, and all the ones after it
            del selected[current_priority:len(selected)] # Remove the pledge we just found, and all the ones after it
            priority = range(0,len(ids)) # Re-cache the priorities

            logger.debug('Priority reached - ' + str(pledge_priority_reached) + ', Left ids - ' + pprint.pformat(ids))

            # If the top priority is reached or there are no more pledges to check, then exit
            if (not args.no_priority and pledge_priority_reached == 0) or not ids:
                sys.exit(0)
            break   # Otherwise, keep going

    print [str(s[2]) for s in selected]

    # pprint.pprint(selected)

    time.sleep(60 * args.interval) # sleep until the next try