import Config
import slack

class SlackService():

    def __init__(self):
        print(str(slack))
        self.client = slack.WebClient(token=Config.config['slack_token'])


    def sendExpertMessage(self, channel, fname, gname, expert_url, institution, product, question):
        response = self.client.chat_postMessage(
            channel=channel,
            text=self.composeMessage(fname, gname, expert_url, institution, product, question))
        
        print("Response: " + str(response))

    def composeMessage(self, fname, gname, expert_url, institution, product, question):
        return(f"We have a question!\r\n" \
                f"\r\n" \
                f"User: {fname} {gname}\r\n" \
                f"Institution: {institution}\r\n" \
                f"Product: {product}\r\n" \
                f"\r\n" \
                f"Question:\r\n" \
                f"{question}\r\n" \
                f"\r\n" \
                f"Collab Link: {expert_url}\r\n" \
                f"\r\n" \
                f"If you pick this up, please first reply with a thread saying you got it so others can take other questions.\r\n" \
                f"\r\n" \
                f"Thanks for being an expert!!")