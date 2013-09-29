from django_socketio.events import Namespace
from socketio.mixins import BroadcastMixin
from socketio.namespace import BaseNamespace


GAME_STATES = {
    "AVAILABLE": 1,
    "INGAME": 2,
    "WAITING": 3,
}

@Namespace('/users')
class UserNamespace(BaseNamespace, BroadcastMixin):
    users = []
    logged_in = {}

    def on_join(self, user):
        #import ipdb; ipdb.set_trace();
        if not 'gamestate' in user:
            user['gamestate'] = GAME_STATES['AVAILABLE']
        if any(filter(lambda u: u['username'] == user['username'], self.users)):
            self.error("user_connected", "User is connected")     
            self.logged_in[user['username']] = self.socket.sessid
        else:
            self.logged_in[user['username']] = self.socket.sessid
            self.users.append(user)
            print 'JOIN ' + user['username']
            self.broadcast_event_not_me('connected', user)
        print self.users
        self.emit('join', self.users)
        
    def recv_disconnect(self):
        user_list = filter(lambda (user, sessid):sessid==self.socket.sessid, self.logged_in.items())

        if any(user_list):            
            self.logged_in.pop(user_list[0][0])
            user = [user for user in self.users if user['username'] == user_list[0][0]][0]
            self.users.remove(user)
            self.broadcast_event_not_me('left', user)
        return True
    


@Namespace('/game')
class GameNamespace(BaseNamespace, BroadcastMixin):
    """
    {
    game_id: {
        users: [{'username': '', 'sessid': '' }, {'username': '', 'sessid': '' }]
        game_board: [[]]
    }

    """
    games = {}

    def on_join(self, game_data):
        username = game_data['username']
        game_id = game_data['game_id']
        if game_id in games:
            games[game_id]['username'].append({'username':username, 'sessid': self.socket.sessid})
            self.emit('start')
        else:
            games[game_id] = {
                              'users': [{'username':username, 'sessid': self.socket.sessid}],
                              'game_board': []
                              }
        
        
    def on_report_click(self, tile):
        pass

    def on_report_result(self, tile):
        pass

    def get_receiver(self, game_id, username):
        for user in self.games[game_id]['users']:
            if user['username'] == username:
                sessid = user['sessid']
        return sessid

    def get_players(self, game_id):
        return [user['sessid'] for user in self.games[game_id]['users']]

    def broadcast_to_user(self, event, receiver_sessid, *args):
        """
        This is sent to all in the sockets in this particular Namespace,
        including itself.
        """
        pkt = dict(type="event",
                   name=event,
                   args=args,
                   endpoint=self.ns_name)

        for sessid, socket in self.socket.server.sockets.iteritems():
            if sessid == receiver_sessid:
                socket.send_packet(pkt)

    def broadcast_to_players(self, event, receivers_sessid, *args):
        """
        (ses_id, ses_id)
        """
        pkt = dict(type="event",
                   name=event,
                   args=args,
                   endpoint=self.ns_name)

        for sessid, socket in self.socket.server.sockets.iteritems():
            if sessid in receivers_sessid:
                socket.send_packet(pkt)