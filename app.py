import datetime
import os
import pprint
import uuid
from urllib.parse import urlparse
from tempfile import mkdtemp
from flask import Flask, jsonify, request, render_template, url_for, redirect
from forms import QuestionForm
import Config
from flask_caching import Cache
from werkzeug.exceptions import Forbidden
from pylti1p3.contrib.flask import FlaskOIDCLogin, FlaskMessageLaunch, FlaskRequest
from pylti1p3.tool_config import ToolConfJsonFile
from flask_sslify import SSLify
import AskAnExpert
from learn.controllers import RestAuthController
from learn.controllers import RestUserController
import ptvsd
import urllib
import webbrowser
import json

app = Flask('ask-an-expert', template_folder='templates', static_folder='static')
config = {
    "DEBUG": False,
    "ENV": "production",
    "CACHE_TYPE": "simple",
    "CACHE_DEFAULT_TIMEOUT": 600,
    "SECRET_KEY": "EF186261-4F2E-4CCC-9C5C-6935CF0262F4",
    "SESSION_TYPE": "filesystem",
    "SESSION_FILE_DIR": mkdtemp(),
    "SESSION_COOKIE_NAME": "flask-session-id",
    "SESSION_COOKIE_HTTPONLY": True,
    "SESSION_COOKIE_SECURE": True,  # should be True in case of HTTPS usage (production)
    "SESSION_COOKIE_SAMESITE": "None"  # should be 'None' in case of HTTPS usage (production)
}
app.config.from_mapping(config)
cache = Cache(app)

if 'DYNO' in os.environ: # only trigger SSLify if the app is running on Heroku
    sslify = SSLify(app)

PAGE_TITLE = 'Ask an Expert'

user_info=None
product=None


class ExtendedFlaskMessageLaunch(FlaskMessageLaunch):

    def validate_nonce(self):
        """
        Probably it is bug on "https://lti-ri.imsglobal.org":
        site passes invalid "nonce" value during deep links launch.
        Because of this in case of iss == http://imsglobal.org just skip nonce validation.
        """
        iss = self._get_iss()
        deep_link_launch = self.is_deep_link_launch()
        if iss == "http://imsglobal.org" and deep_link_launch:
            return self
        return super(ExtendedFlaskMessageLaunch, self).validate_nonce()


def get_lti_config_path():
    return os.path.join(app.root_path, 'configs', 'lti.json')


@app.route('/check-cookies-allowed/', methods=['GET'])
def check_cookies_allowed():
    print("In Check Cookies...")
    test_cookie_val = request.cookies.get('test_cookie', None)
    print("test_cookie_val: " + test_cookie_val)
    request_ts = request.args.get('ts', None)
    print("ts: " + request_ts)
    cookie_sent = bool(request_ts and test_cookie_val and request_ts == test_cookie_val)
    print("cookie sent: " + str(cookie_sent))
    return jsonify({'cookies_allowed': cookie_sent})


@app.route('/login/', methods=['GET', 'POST'])
def login():
    cookies_allowed = str(request.args.get('cookies_allowed', ''))

    # check cookies and ask to open page in the new window in case if cookies are not allowed
    # https://chromestatus.com/feature/5088147346030592
    # to share GET/POST data between requests we save them into cache
    if cookies_allowed:
        login_unique_id = str(request.args.get('login_unique_id', ''))
        if not login_unique_id:
            raise Exception('Missing "login_unique_id" param')

        login_data = cache.get(login_unique_id)
        if not login_data:
            raise Exception("Can't restore login data from cache")

        tool_conf = ToolConfJsonFile(get_lti_config_path())

        request_params_dict = {}
        request_params_dict.update(login_data['GET'])
        request_params_dict.update(login_data['POST'])

        oidc_request = FlaskRequest(request_data=request_params_dict)
        oidc_login = FlaskOIDCLogin(oidc_request, tool_conf)
        target_link_uri = request_params_dict.get('target_link_uri')
        return oidc_login.redirect(target_link_uri)
    else:
        login_unique_id = str(uuid.uuid4())
        cache.set(login_unique_id, {
            'GET': request.args.to_dict(),
            'POST': request.form.to_dict()
        }, 3600)
        tpl_kwargs = {
            'login_unique_id': login_unique_id,
            'same_site': app.config['SESSION_COOKIE_SAMESITE'],
            'page_title': PAGE_TITLE
        }
        return render_template('check_cookie.html', **tpl_kwargs)


@app.route('/launch/', methods=['HEAD','GET','POST'])
def launch():
    launch_unique_id = str(request.args.get('launch_id', ''))
    
    print("launch_unique_id: " + launch_unique_id)
    
    # reload page in case if session cookie is unavailable (chrome samesite issue):
    # https://chromestatus.com/feature/5088147346030592
    # to share GET/POST data between requests we save them into cache
    session_key = request.cookies.get(app.config['SESSION_COOKIE_NAME'], None)
    
    if not session_key:
        print("session_key: None")
    else:
        print("session_key: " + session_key)

    if not session_key and not launch_unique_id:
        launch_unique_id = str(uuid.uuid4())
        cache.set(launch_unique_id, {
            'GET': request.args.to_dict(),
            'POST': request.form.to_dict()
        }, 3600)
        current_url = request.base_url

        parsed_url = urlparse(current_url)
        parsed_url = parsed_url._replace(scheme='https')

        current_url = parsed_url.geturl() 

        if '?' in current_url:
            current_url += '&'
        else:
            current_url += '?'
        current_url = current_url + 'launch_id=' + launch_unique_id

        return '<script type="text/javascript">window.location="%s";</script>' % current_url
        
    launch_request = FlaskRequest()
    if request.method == "GET":
        launch_data = cache.get(launch_unique_id)
        print("launch_data: " + str(launch_data))
        if not launch_data:
            raise Exception("Can't restore launch data from cache")
        request_params_dict = {}
        request_params_dict.update(launch_data['GET'])
        request_params_dict.update(launch_data['POST'])
        print("request_params_dict: " + str(request_params_dict))
        launch_request = FlaskRequest(request_data=request_params_dict)

    print("launch_request: " + str(launch_request))
    tool_conf = ToolConfJsonFile(get_lti_config_path())
    print("tool_conf: " + str(tool_conf))
    message_launch = ExtendedFlaskMessageLaunch(launch_request, tool_conf)
    print("message_launch: " + str(message_launch))
    message_launch_data = message_launch.get_launch_data()
    pprint.pprint(message_launch_data)

    learn_url = message_launch_data['https://purl.imsglobal.org/spec/lti/claim/tool_platform']['url'].rstrip('/')

    tpl_kwargs = {
        'page_title': PAGE_TITLE,
        'is_deep_link_launch': message_launch.is_deep_link_launch(),
        'launch_data': message_launch.get_launch_data(),
        'launch_id': message_launch.get_launch_id(),
        'family_name': message_launch_data.get('family_name', ''),
        'given_name': message_launch_data.get('given_name', ''),
        'user_email': message_launch_data.get('email', ''),
        'user_uuid': message_launch_data.get('sub', ''),
        'learn_url': learn_url

    }

    print("tpl_kwargs: " + str(tpl_kwargs))

    params = {
        'redirect_uri' : 'https://ask-an-expert.herokuapp.com/authcode/',
        'response_type' : 'code',
        'client_id' : Config.config['learn_rest_key'],
        'scope' : '*',
        'state' : str(uuid.uuid4())
    }

    encodedParams = urllib.parse.urlencode(params)

    get_authcode_url = learn_url + '/learn/api/public/v1/oauth2/authorizationcode?' + encodedParams

    return(redirect(get_authcode_url))

@app.route('/authcode/', methods=['GET', 'POST'])
def authcode():
    
    authcode = request.args.get('code', '')
    state = request.args.get('state', '')
    print (authcode)
    
    restAuthController = RestAuthController.RestAuthController(authcode)
    restAuthController.setToken()
    token = restAuthController.getToken()
    uuid = restAuthController.getUuid()

    restUserController = RestUserController.RestUserController(Config.config['learn_rest_url'], token)
    global user_info 
    user_info = restUserController.getUserInfoFromLearn()

    courseIds = Config.courseIds
    contentIds = Config.contentIds

    tpl_kwargs = {
        'page_title': PAGE_TITLE,
        'learn_url' : 'https://bbworld.hopto.org',
        'token' : token,
        'user_info' : user_info,
        'content_ids' : contentIds,
        'course_ids' : courseIds
    }

    print("authcode tpl_kwargs: " + str(tpl_kwargs) )

    return render_template('index.html', **tpl_kwargs)
    
@app.route('/renderform/', methods=['GET', 'POST'])
def renderform():
    global user_info, product

    data = json.loads(request.args.get('data', ''))

    print("routeData: " + str(data))

    contentId = data['contentId']
    print("Content Id: " + contentId)

    product = Config.contents[contentId]

    print("Product: " + product)

    form = QuestionForm.QuestionForm(user_info)
    
    known_values = {}

    try:
        if user_info['name']:
            known_values['gname'] = user_info['name']['given'] if user_info['name']['given'] != None else 'Unknown'
            known_values['fname'] = user_info['name']['family'] if user_info['name']['family'] != None else 'Unknown'
        else:
            known_values['gname'] = 'Unknown'
            known_values['fname'] = 'Unknown'
    except KeyError:
        known_values['gname'] = 'Unknown'
        known_values['fname'] = 'Unknown'

    try:    
        if user_info['contact']:
            known_values['email'] = user_info['contact']['email'] if user_info['contact']['email'] != None else 'Unknown'
        else:
            known_values['email'] = 'Unknown'
    except KeyError:
        known_values['email'] = 'Unknown'
        
    try:
        if user_info['job']:
            known_values['institution'] = user_info['job']['company'] if user_info['job']['company'] != None else 'Unknown'
        else:
            known_values['institution'] = 'Unknown'
    except KeyError:
        known_values['institution'] = 'Unknown'

    known_values['uuid'] = user_info['uuid'] if user_info['uuid'] != None else 'Unknown'
    known_values['product'] = product if product != "" and product !=None else 'Unknown'
    
    return render_template('question.html', form=form, user_info=known_values)

@app.route('/question/', methods=['POST'])
def question():
    global user_info, product

    form = QuestionForm.QuestionForm(request.form)
   
    gname = form.gname.data if form.gname.data != "" and form.gname.data != None else user_info['name']['given']
    fname = form.fname.data if form.fname.data != "" and form.fname.data != None else user_info['name']['family']
    email = form.email.data if form.email.data != "" and form.email.data != None else user_info['contact']['email']
    institution = form.institution.data if form.institution.data != "" and form.institution.data != None else user_info['job']['company']

    uuid = user_info['uuid'] if user_info['uuid'] != None else str(uuid.uuid4())
    
    print("product: " + product + ", form.product.data: " + form.product.data)
    prod = product if product != "" and product != None else form.product.data
    print("prod: " + prod)
    question = form.question.data

    askAnExpert = AskAnExpert.AskAnExpert()
    client_url = askAnExpert.createRoom(gname, fname, email, institution, prod, question, uuid)

    return render_template('launch_collab.html', collab_url=client_url)

if __name__ == '__main__':
    restAuthController = None
    port = int(os.environ.get('PORT', 33507))
    app.run(host='0.0.0.0', port=port)