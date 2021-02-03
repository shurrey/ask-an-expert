from collab import Collab
from slackmodule import SlackService


class AskAnExpert():

    def __init__(self):
        pass

    def createRoom(self,gname,fname,email,institution,product,question, uuid):
        collab_service = Collab.Collab()
        slack_service = SlackService.SlackService()

        session_json = collab_service.createExpertSession(gname,fname,email,institution,product,question, uuid)

        expert_url = session_json['expert_url']
        client_url = session_json['client_url']
        
        print('Expert URL: ' + expert_url + '\r\n')
        print('Client URL: ' + client_url)

        slack_service.sendExpertMessage('#knowledgebar', gname, fname, expert_url, institution, product, question)

        return(client_url)
        
        