from collab import Collab
from slackmodule import SlackService


collab_service = Collab.Collab()
slack_service = SlackService.SlackService()

session_json = collab_service.createExpertSession('Albert','Einstein','albert.einstein@genius.edu','Genius University','Astrophysics 101','What does the C stand for in E=MC-squared?')

expert_url = session_json['expert_url']
client_url = session_json['client_url']

print('Expert URL: ' + expert_url + '\r\n')
print('Client URL: ' + client_url)

slack_service.sendExpertMessage('#officehours', 'Albert','Einstein', expert_url, 'Genius University','Astrophysics 101','What does the C stand for in E=MC-squared?')

print(client_url)