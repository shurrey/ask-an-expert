'''
Copyright (C) 2016, Blackboard Inc.
All rights reserved.
Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
Neither the name of Blackboard Inc. nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.
THIS SOFTWARE IS PROVIDED BY BLACKBOARD INC ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL BLACKBOARD INC. BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on May 25, 2016

@author: shurrey
'''

import sys
import os
import getopt
import datetime
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import Config
import Config

# Import Controllers
from collab.controllers import AuthController
from collab.controllers import UserController
from collab.controllers import SessionController

# Import Models
from collab.models import User
from collab.models import Session

class Collab():

    def __init__ (self):
        self.URL = Config.config['collab_base_url']
        self.SURVEY_URL = Config.config['survey_url']
        self.COLLAB_KEY = Config.config['collab_key']
        self.COLLAB_SECRET = Config.config['collab_secret']

        if Config.config['verify_certs'] == 'True':
            self.COLLAB_CERTS = True
        else:
            self.COLLAB_CERTS = False

        self.session_name = 'Knowledge Bar'
        self.session_description = 'Talk to Blackboard Experts. Ask your questions, and get answers.'
        
    def createExpertSession(self,gname,fname,email,institution,product,question, extId):

        print ('\n[main] Acquiring auth token...\n')
        authorized_session = AuthController.AuthController(self.URL,self.COLLAB_KEY,self.COLLAB_SECRET,self.COLLAB_CERTS)
        authorized_session.setToken()
        print ('\n[main] Returned token: ' + authorized_session.getToken() + '\n')

        user = User.User(gname, fname, gname + " " + fname + "(" + institution + ")", extId, email)

        print("User: " + str(user.getUserJson()))

        users = UserController.UserController(self.URL, authorized_session.getToken(), self.COLLAB_CERTS)
        
        clientUserId = users.createUser(user.getUserJson())
        user.setId(clientUserId)
        
        smeUserId = users.createUser({'displayName' : 'Blackboard', 'extId' : 'sme'})

        print('Client User Id: ' + clientUserId)
        print('SME User Id: ' + smeUserId)

        session = Session.Session(self.session_name, self.session_description, self.SURVEY_URL)

        sessions = SessionController.SessionController(self.URL, authorized_session.getToken(), self.COLLAB_CERTS)

        session_id = sessions.createSession(session.getSessionJson())

        print('Session Id: ' + session_id)

        smeJson = {
            'id' : smeUserId,
            'displayName' : 'Blackboard',
            'extId' : 'sme'
        }

        smeUrl = sessions.enrollUser(session_id, smeJson, "moderator")
        clientUrl = sessions.enrollUser(session_id, user.getUserJson(), "presenter")


        print("Client URL: " + clientUrl)
        print("SME URL: " + smeUrl)

        print("[main] Processing Complete")

        return({ 'expert_url' : smeUrl, 'client_url' : clientUrl})

    