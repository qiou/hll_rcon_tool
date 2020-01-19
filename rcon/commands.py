from dataclasses import dataclass
from functools import wraps

from rcon.connection import HLLConnection

@dataclass
class Admin:
    steam_id_64: str
    role: str
    name: str


def escape_string(s):
    """ Logic taken from the official rcon client. 
    There's probably plenty of nicer and more bulletproof ones
    """
    quoted = ""
    for idx, char in enumerate(s):
        if char != '"':
            if char != '\\':
                quoted += char
            else:
                quoted += "\\\\"
        else:
            quoted += "\\\""
    return quoted


def _escape_params(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(args)
        return func(
            args[0],
            *[escape_string for a in args[1:]],
            **{k: v for k, v in kwargs.items()}
        )
    return func

    
class ServerCtl:
    """TODO: Use string format instead of interpolation as it could be a
    security risk

    set password not implemented on purpose
    """
    def __init__(self, config):
        self.conn = HLLConnection()
        self.conn.connect(
            config['host'],
            config['port'],
            config['password']
        )

    def _request(self, command: str):
        self.conn.send(command.encode())
        return self.conn.receive().decode()
    
    def _get(self, item, is_list=False):
        res = self._request(f"get {item}")
        
        if not is_list:
            return res
        
        res = res.split('\t')
        if res[-1] == '':
            # There's a trailin \t
            res = res[:-1]
        expected_len = int(res[0])
        actual_len = len(res) - 1 
        if expected_len != actual_len:
            raise RuntimeError(
                f"Server returned incomplete list,"
                f" expected {expected_len} got {actual_len}"
            )
        return res[1:]
        
    def get_name(self):
        return self._get("name")

    def get_map(self):
        # server adds a _RESTART suffix after the name when the map is
        # loading
        return self._get("map")

    def get_maps(self):
        return self._get("mapsforrotation", True)

    def get_players(self):
        return self._get("players", True)

    @_escape_params
    def get_player_info(self, player_name):
        return self._request(f"playerinfo {player_name}")
        
    def get_admin_ids(self):
        admins = []
        for admin in self._get("adminids", True):
            id_, role, name = admin.split(' ')
            admins.append(Admin(steam_id_64=id_, role=role, name=name[1:-1]))
        return admins
        
    def get_temp_bans(self):
        return self._get("tempbans", True)

    def get_perma_bans(self):
        return self._get("permabans", True)
    
    def get_team_switch_cooldown(self):
        return self._get("teamswitchcooldown")

    def get_autobalance_threshold(self):
        return self._get("autobalancethreshold")

    def get_map_rotation(self):
        return self._request('rotlist').split('\n')[:-1]

    def get_slots(self):
        return self._get("slots")

    def get_vip_ids(self):
        return self._get("vipids", True)

    def get_admin_groups(self):
        return self._get("admingroups", True)
    
    def get_logs(self, since_min_ago, filter_=''):
        return self._request(f'showlog {since_min_ago}')

    def get_idle_autokick_time(self):
        return self._get("idletime")

    def get_max_ping_autokick(self):
        return self._get('highping')

    def get_queue_length(self):
        return self._get("maxqueuedplayers")

    def get_vip_slots_num(self):
        return self._get("numvipslots")

    def set_autobalance(self, bool_str):
        """
        String bool is on / off
        """
        return self._request(f'setautobalanceenabled {bool_str}')
    
    def set_welcome_message(self, msg):
        return self._request(f"say {msg}")

    def set_map(self, map_name):
        return self._request(f"map {map_name}")

    def set_idle_autokick_time(self, minutes):
        return self._request(f"setkickidletime {minutes}")

    def set_max_ping_autokick(self, max_ms):
        return self._request(f"sethighping {max_ms}")

    def set_autobalance_threshold(self, max_diff: int):
        return self._request(f"setautobalancethreshold {max_diff}")

    def set_team_switch_cooldown(self, minutes):
        return self._request(f"setteamswitchcooldown {minutes}")

    def set_queue_length(self, num):
        return self._request(f"setmaxqueuedplayers {num}")

    def set_vip_slots(self, num):
        return self._request(f"setnumvipslots {num}")
                             
    @_escape_params
    def set_broadcast(self, msg):
        return self._request(f'broadcast "{msg}"')

    @_escape_params
    def do_switch_player_on_death(self, player):
        return self._request(f'switchteamondeath "{player}"')

    def do_swtich_player_now(self, player):
        return self._request(f'switchteamnow "{player}"')
    
    def do_add_map_to_rotation(self, map_name):
        return self._request(f"rotadd {map_name}")

    def do_remove_map_from_rotation(self, map_name):
        return self._request(f"rotdel {map_name}")
    
    @_escape_params
    def do_punish(self, player):
        return self._request(f'punish "{player}" "{reason}"')
    
    @_escape_params
    def do_kick(self, player):
        return self._request(f'kick "{player}" "{reason}"')
    
    @_escape_params
    def do_temp_ban(self, player, reason):
        return self._request(f'tempban "{player}" "{reason}"')

    @_escape_params
    def do_perma_ban(self, player, reason):
        return self._request(f'permaban "{player}" "{reason}"')

    def do_remove_temp_ban(self, ban_log):
        return self._request(f"pardontempban {ban_log}")

    def do_remove_perma_ban(self, ban_log):
        return self._request(f"pardonpermaban {ban_log}")

    @_escape_params
    def do_add_admin(self, steam_id_64, role, name):
        return self._request(f'adminadd "{steam_id_64}" "{role}" "{name}"')

    def do_remove_admin(self, steam_id_64):
        return self._request(f'admindel {steam_id_64}')

    @_escape_params
    def do_add_vip(self, steam_id_64, name):
        return self._request(f'vipadd {steam_id_64} "{name}"')

    def do_remove_vip(self, steam_id_64):
        return self._request(f'vipdel {steam_id_64}')
    
if __name__ == '__main__':
    import os
    from rcon.settings import SERVER_INFO
    
    ctl = ServerCtl(
        SERVER_INFO
    )
    
    print(ctl.get_map())
    maps = ctl.get_map_rotation()
    #print(ctl.set_map(maps[2]))
    print(ctl.get_map())