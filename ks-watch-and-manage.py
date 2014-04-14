#!/usr/bin/env python

# Copyright 2013, Timur Tabi
# Copyright 2014, Prakhar Birla
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
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.in_form_block = False    # True == we're inside an <form class='...'> block
        self.in_script_block = False # True == we're inside a <script> block

    def process(self, url) :
        while True:
            try:
                f = urllib2.urlopen(url)
                break
            except urllib2.HTTPError as e:
                print 'HTTP Error', e
            except urllib2.URLError as e:
                print 'URL Error', e
            except Exception as e:
                print 'General Error', e

            print 'Retrying in one minute'
            time.sleep(60)

        html = unicode(f.read(), 'utf-8')
        f.close()
        self.rewards = []
        self.form_hidden_inputs = {}
        self.json_variables = {}

        self.feed(html)   # feed() starts the HTMLParser parsing

        # if the json variable current_project was loaded, then
        # move information contained in the respective fields
        if 'current_project' in self.json_variables:
            for reward in self.json_variables['current_project']['rewards']:
                if 'limit' in reward: # only put limited rewards
                    self.rewards.append((
                        float(reward['minimum']),
                        reward['remaining'],
                        str(reward['remaining']) + ' of ' + str(reward['limit']),
                        reward['project_id'],
                        reward['reward'],
                        float(reward['shipping_amount']) if reward['shipping_applicable'] else 0.0))
        
        self.logged_in = True if 'current_user' in self.json_variables else False

        self.pre_pledged = {'amount':self.json_variables['current_checkout']['amount'],
        'id':self.json_variables['current_checkout']['reward']['id']} if 'current_checkout' in self.json_variables and self.json_variables['current_checkout']['amount'] > 0 else {'amount':0,'id':0}

        pprint.pprint(self.rewards)
        pprint.pprint(self.pre_pledged)
        return self.rewards

    def handle_starttag(self, tag, attributes):
        global status

        attrs = dict(attributes)

        if tag == 'script' and len(attrs) == 0:
            self.in_script_block = True

        # TODO instead of this, just read the meta tags
        # and disengage the parsing when the body tag is reached

        # It turns out that we only care about tags that have a 'class' attribute
        if not 'class' in attrs:
            return
        if tag == 'form' and attrs['class'] == 'manage_pledge':
            self.in_form_block = True
        if self.in_form_block and tag == 'input' and attrs['class'] == 'hidden':
            self.form_hidden_inputs[attrs['name']] = attrs['value']

    def handle_endtag(self, tag):
        if tag == 'form':
            self.in_form_block = False

        if tag == 'script':
            self.in_script_block = False

    def handle_data(self, data):
        if self.in_script_block:
            # find the variable we are interested in
            start = data.find("current_");
            # only consider if it's in the beinning
            if start > 0 and start < 30:
                # trim the last 8 chars
                data = data[start:-8]
                if data.count('\n') == 1:
                    # extract the variable name
                    variable_name =  data[:data.find(' ')]
                    # extract the raw json and do a html decode
                    raw_json = self.unescape(data[data.find('= ')+2:data.rfind(';')])
                    # trim quotes, if present
                    if raw_json[0] == '"' and raw_json[-1] == '"':
                        raw_json = raw_json[1:-1]
                    # json decode the string.. i.e. make it an object
                    self.json_variables[variable_name] = json.loads(raw_json)
                    # print variable_name
                    # print raw_json
                    # pprint.pprint(self.json_variables[variable_name])

    # def parse_only_digits(self, data):
    #     amount = data.encode('ascii','ignore')
    #     nondigits = amount.translate(None, '0123456789.')
    #     return amount.translate(None, nondigits)

    def result(self):
        return self.rewards

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
parser.add_argument("-v", "--verbose", action="store_true",
    help="ask questions to set up the options")
parser.add_argument("-pa", "--pledge-amount", action='store_true',
    help="pledges specified in terms of the currency amount")
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
parser.add_argument("-d", "--destroy", action="store_true",
    help="destroy (/cancel) pledge if the required pledge(s) couldn't be" +
    " selected (requires cookies)")
parser.add_argument("-dt", "--destroy-threshhold", type=int,
    choices=xrange(1, 11), default=5,
    help="time (in minutes) to project completion to destroy (cancel) the pledge" +
    " (default: %(default)s) (requires cookies)")
parser.add_argument("-p", "--pledge", nargs="*", type=int,
    help="pledges (numbers separated by spaces) ordered" +
    " by priority, highest to lowest")
args = parser.parse_args()

pprint.pprint(args)
sys.exit(0)

# Generate the URL
url = args.url.split('?', 1)[0]  # drop the stuff after the ?
base_url = url
url += '/pledge/new' # we want the pledge-editing page
pledges = None   # The pledge amounts on the command line
ids = None       # A list of IDs of the pledge levels
selected = None  # A list of selected pledge levels
rewards = None   # A list of valid reward levels
use_credentials = False

status_changed = False

stats = None   # A list of the initial statuses of the selected pledge level
priority = None

ks = KickstarterHTMLParser()

if args.cookies:
    cj = cookielib.MozillaCookieJar(args.cookies.name)
    cj.load()
    cookie_opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    use_credentials = True

proxy_handler = urllib2.ProxyHandler({})
blank_opener = urllib2.build_opener(proxy_handler)
urllib2.install_opener(blank_opener)

test_completed = False

while True:

    if use_credentials:
        print 'Fetching the page with user credentials'
        urllib2.install_opener(cookie_opener)
        use_credentials = False
    else:
        urllib2.install_opener(blank_opener)

    rewards = ks.process(url)

    if not rewards:
        print 'No limited rewards for this Kickstarter'
        sys.exit(0)

    if ids:
        selected = [r for r in rewards if r[3] in ids]
    else:
        if pledges:
            selected = [r for r in rewards if r[0] in pledges]
        else:
            # If a pledge amount was not specified on the command-line, then prompt
            # the user with a menu
            selected = pledge_menu(rewards)

        ids = [s[3] for s in selected]
        stats = [s[1] for s in selected]
        priority = range(0,len(ids))
        pledge_priority_reached = len(ids) + 1

    for stat, s, id, current_priority in zip(stats, selected, ids, priority):
        if stat != s[1] or s[2] == 'Unlimited':

            if not status_changed:
                print 'Status changed!'
                use_credentials = True
                
                status_changed = True
            else:
                print 'Creating re-pledge request'
                submit_data = ks.form_hidden_inputs
                # urllib.encode doesn't support encoding of utf8 characters
                submit_data['utf8'] = ''
                submit_data['backing[amount]'] = s[0]
                if submit_data['backing[domestic]'] == '0':
                    submit_data['backing[amount]'] += s[5] #international shipping
                submit_data['backing[backer_reward_id]'] = id
                data = urllib.urlencode(submit_data)

                result = urllib2.urlopen(url=post_url, data=data).read()

                print 'Re-pledged!!!'

                pledge_priority_reached = current_priority
                ids = [x for x in ids if x != id]   # Remove the pledge we just found
                priority.pop()


            # webbrowser.open_new_tab(url)

            #ids = [x for x in ids if x != id]   # Remove the pledge we just found

            # If there are no more pledges to check or the top priority is reached, then exit
            if not ids or pledge_priority_reached == 0:
                time.sleep(10)   # Give the web browser time to open
                sys.exit(0)
            break   # Otherwise, keep going

    print [str(s[2]) for s in selected]

    # pprint.pprint(selected)

    if not status_changed:
        time.sleep(60)