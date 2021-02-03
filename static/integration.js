/*
 * Copyright (C) 2019, Blackboard Inc.
 * All rights reserved.
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 *  -- Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 *
 *  -- Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 *  -- Neither the name of Blackboard Inc. nor the names of its contributors
 *     may be used to endorse or promote products derived from this
 *     software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY BLACKBOARD INC ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL BLACKBOARD INC. BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 * LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 * ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

// Verify that we're in the integration iframe
if (!window.parent) {
    throw new Error('Not within iframe');
  }
  
  //const integrationHost = `${window.location.protocol}//${window.location.hostname}:${window.location.port}`;
  const integrationHost = learn_url;
  const shouldShowPanel = true;
  const launchUrl = launch_url;
  const contents = content_ids.split(',');
  const courses = course_ids.split(',');
  let messageChannel;
  let panelId;
  const getIframeSrc = () => launchUrl;
  
  const getContents = () => {
    return({
      tag: 'iframe',
      props: {
        src: getIframeSrc(),
        style: {
          padding: containerPadding
        }
      }
    });
  };
  
    // Set up the window.postMessage listener for the integration handshake (for
    // step #2)
    console.log("addEventListener");
    window.addEventListener("message", onPostMessageReceived, false);
  
  // (1) Send the integration handshake message to Learn Ultra. This notifies
  // Learn Ultra that the integration has
  // loaded and is ready to communicate.
  console.log("say hello to " + integrationHost);
  window.parent.postMessage({"type": "integration:hello"}, integrationHost + '/*');
  
  function onPostMessageReceived(evt) {
    // Do some basic message validation.
    console.log("whoop! whoop! Got a message! " + evt.origin);
    const fromTrustedHost = evt.origin === window.__lmsHost || evt.origin === integrationHost;
    console.log("fromTrustedHost: " + fromTrustedHost)
    console.log("evt.data: " + evt.data)
    console.log("evt.data.type: " + evt.data.type)
    if (!fromTrustedHost || !evt.data || !evt.data.type) {
      return;
    }
    console.log("passed validation, event type is " + evt.data.type);
    // (2) A majority of the communication between the integration and Learn
      // Ultra will be over a "secure" MessageChannel.
    // As response to the integration handshake, Learn Ultra will send a
      // MessageChannel port to the integration.
    if (evt.data.type === 'integration:hello') {
      // Store the MessageChannel port for future use
      messageChannel = new LoggedMessageChannel(evt.ports[0]);
      messageChannel.onmessage = onMessageFromUltra;
  
      // (3) Now, we need to authorize with Learn Ultra using the OAuth2 token
      // that the server negotiated for us
      console.log("authorize with token " + token);
      messageChannel.postMessage({
        type: 'authorization:authorize',
  
        // This token is passed in through integration.ejs
        token: token
      });
    }
  
  }
  
  function onMessageFromUltra(message) {
    // (4) If our authorization token was valid, Learn Ultra will send us a
      // response, notifying us that the authorization
    // was successful
    console.log("Got a message from Ultra: " + message.data.type);
    if (message.data.type === 'authorization:authorize') {
      onAuthorizedWithUltra();
    }
  
    // (7) On click, route, and hover messages, we will receive an event:event
      // event
    if (message.data.type === 'event:event') {
      // From here, you can do something with those events...
      if(message.data.eventType === 'click') {
        console.log(message.data.analyticsId);
      }
      
      if (message.data.eventType === 'route') {
        console.log("routeName: " + message.data.routeName);
        console.log("courses: " + courses)
        console.log("contents: " + contents)
        console.log("CourseId: " + message.data.routeData.courseId)
        console.log("ContentId: " + message.data.routeData.contentId)
        console.log("has course: " + courses.indexOf (message.data.routeData.courseId) >= 0)
        console.log("has content: " + contents.indexOf (message.data.routeData.contentId) >= 0)
        
        if(courses.indexOf (message.data.routeData.courseId) >= 0 && contents.indexOf (message.data.routeData.contentId) >= 0) {
        
          if (shouldShowPanel && (message.data.routeName === 'base.recentActivity.peek.course.outline.peek.discussion.view.with-grading')) {
            localStorage.setItem('context', JSON.stringify(message.data.routeData));
            
            setTimeout(() => {
              // (8) For demo purposes, we will open a panel. We send a message to
                // Ultra requesting a panel be
              // opened (if shouldShowPanel is enabled)
              messageChannel.postMessage({
                type: 'portal:panel',
                correlationId: 'panel-1',
                panelType: 'small',
                panelTitle: 'Virtual Knowledge Bar',
                attributes: {
                  onClose: {
                    callbackId: 'panel-1-close',
                  },
                  onClick: {
                    callbackId: 'panel-1-close',
                  },
                },
              });
            }, 2000);
          }
        }
      }
    }
  
    // (9) Once Ultra has opened the panel, it will notify us that we can render
      // into the panel
    if (message.data.type === 'portal:panel:response') {
      renderPanelContents(message);
    }
  
    // (10) When the help button has been clicked, we'll use the registered help
      // provider
    if (message.data.type === 'help:request') {
      // for demo purposes we'll just open Google's home page
      window.open(launchUrl);
      sendMessage({
        "type": "help:request:response",
        "correlationId": msg.data.correlationId
      });
    }
  }
  
  function onAuthorizedWithUltra() {
    console.log('Authorization was successful');
  
    // (5) Once we are authorized, we can subscribe to events, such as telemetry
      // events
    messageChannel.postMessage({
      type: 'event:subscribe',
      subscriptions: ['click','route','portal:new','portal:remove'],
    });
  
    // (6) We can also register a help provider, such as a primary help provider
      // that will overwrite the existing provider
   /* messageChannel.postMessage({
      type: 'help:register',
      id: 'google-help-provider',
      displayName: 'Google',
      iconUrl: 'https://www.google.com/images/branding/googleg/1x/googleg_standard_color_128dp.png',
      providerType: 'primary'
    });*/
  }
  
  function renderPanelContents(message) {
    // (9) Notify Ultra to render our contents into the panel
    if (message.data.correlationId === 'panel-1') {
      var launchUrl2 = launchUrl + '?data='+ encodeURIComponent(localStorage.getItem('context'))
      panelId = message.data.portalId;
      messageChannel.postMessage({
        type: 'portal:render',
        portalId: message.data.portalId,
        contents: {
          tag: 'span',
          props: {
            style: {
              display: 'flex',
              height: '100%',
              width: '100%',
              flexDirection: 'column',
              alignItems: 'stretch',
              justifyContent: 'stretch',
            },
          },
          children: [{
            tag: 'iframe',
            props: {
              style: {
                  flex: '1 1 auto',
              },
              src: launchUrl2,
            },
          }]
        },
      });
    }
  }
  
  // Sets up a way to communicate between the iframe and the integration script
  window.addEventListener('storage', onEventFromIframe);
  function onEventFromIframe(evt) {
    console.log("In event from Iframe key: " + evt.key + " full event: " + evt)
    if (evt.key !== 'event') {
      return;
    }
  
    const message = JSON.parse(evt.newValue);
    switch (message.type) {
      // Handles when the user clicks the "close panel" button
      case 'portal:panel:close':
        messageChannel.postMessage({
          type: 'portal:panel:close',
          id: panelId,
        });
        break;
    }
  }
  
  /**
   * A MessageChannel-compatible API, but with console logging.
   */
  class LoggedMessageChannel {
    onmessage = () => { /* */
      console.log('test');
    };
  
    constructor(messageChannel) {
      this.messageChannel = messageChannel;
      this.messageChannel.onmessage = this.onMessage;
    }
  
    onMessage = (evt) => {
      console.log(`[UEF] From Learn Ultra:`, evt.data);
      this.onmessage(evt);
    };
  
    postMessage = (msg) => {
      console.log(`[UEF] To Learn Ultra`, msg);
      this.messageChannel.postMessage(msg);
    }
  }