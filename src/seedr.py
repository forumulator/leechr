import copy
import requests, json

class SeedrAgent:
    """ The selenium seedr agent to help manual login and whatnot """
    pass

# {
#     "result": "not_enough_space_wishlist_full",
#     "code": 200
# }
class Seedr:
    """ Seedr: The class the represents the seedr python API """
    _HEADERS = {
        "Accept": r"application/json, text/javascript, */*; q=0.01",
        "Accept-Encoding": r"gzip, deflate, br",
        "Accept-Language": r"en-US,en;q=0.9",
        "Connection": r"keep-alive",
        "Cookie": r"PHPSESSID=1q429fjo8mb7edj1j9v52j24a1",
        "Host": r"www.seedr.cc",
        "Origin": r"https://www.seedr.cc",
        "Referer": r"https://www.seedr.cc/files/{user_id}",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36",
        "X-Requested-With": r"XMLHttpRequest"
    }
    _SESSION_FILE = ".seedrpy"
    _BASE_URL = "https://www.seedr.cc"
    _ADD_TORRENT = r"/actions.php?action=add_torrent"
    _DELETE = r"/actions.php?action=delete"
    _LIST_CONTENTS = r"/content.php?action=list_contents"

    def __init__(self, user = None, passwd = None):
        self.sess_id, self.user_id = self._last_session_info()
        if not self.sess or not self.user_id or not self._validate_session():
            print("No previous logins found, trying to login")
            self.sess_id, self.user_id = self.login(user, passwd)
            if self._save_session():
                self.logger.error("Couldn't save session: "\
                    + self.sess_id + " " + self.user_id)
        self.headers = copy.deepcopy(Seedr._HEADERS)
        self.headers["Referer"] = self.headers["Referer"].format(
            user_id = self.User)
        self.home_content = None

    # TODO Complete this
    def _validate_session(self):
        """ Validate the session data that we have currently """
        return True

    def _save_session(self):
        """ Save the current session tokens to a file """
        if not self.sess_id or not self.user_id:
            return False
        with open(Seedr._SESSION_FILE, "a") as sess_file:
            print(self.sess_id, self.user_id, file = sess_file)
        return True

    def _last_session_info(self):
        """ Retrieve last session info from file """
        with open(Seedr._SESSION_FILE) as sess_file:
            sess_id, user_id = sess_file.readlines()[-1].split()
        return (sess_id, user_id)

    def login(self, user, passwd):
        if not user or not passwd:
            raise Exception("User or Pass can't be empty")

    def _make_request(self, url, form_data):
        """ Make HTTP POST request to URL with encoded form_data """
        resp = requests.post(url, headers = self.headers, data = form_data)
        if resp.status_code != 200:
            raise Exception("Response status code error")
        return json.loads(response.text)

    def add_torrent_magnet(self, magnet):
        """ Add the magnet to the torrent queue. Return a 2-tuple of
            (torrent_id, title). If an error occurs, torrent_id == -1
            and title is the error_message
        """
        form_data = {
            "torrent_magnet": magnet,
            "folder_id": -1
        }
        resp = self._make_request(Seedr._BASE_URL + Seedr._ADD_TORRENT,
                                  form_data)
        if resp["result"] is not True:
            error_name = resp["error"] if (error in resp) else resp["result"] 
            return (-1, error_name)
        else:
            return (resp["user_torrent_id"], resp["title"])

    def _update_home_contents(self):
        """ Make the list contents call to update the content
            of the home directory
        """
        form_data = {
            "content_type": "folder",
            "content_id": "{user_id}".format(user_id = self.user_id),
        }
        if self.home_content:
            form_data["timestamp"] = self.home_content["timestamp"]
        resp = self._make_request(Seedr._BASE_URL + Seedr._LIST_CONTENTS, 
                                  form_data)
        if not (result in resp and resp["result"] == "no_update"):
            self.home_content = resp

    def list_home_contents(self):
        """ Return a list of home contents """
        self._update_home_contents()
        content_keys = ["torrent", "folders", "files"]
        if self.home_content:
            contents = { key: self.home_content[key] for key in content_keys }
            return contents
        else
            return None

    def is_home_full(self):
        self._update_home_contents()
        return self.home_content["space_used"] < self.home_content["space_max"]

    def is_download_ongoing(self):
        self._update_home_contents()
        # Atleast one active torrent in home
        return len(self.home_content["torrents"]) > 0

    def approx_download_time(self):
        """ ETA till the current ongoing torrent finishes """
        self._update_home_contents()
        if not self.is_download_ongoing():
            return 0
        torrent = self.home_content["torrents"][0]
        approx_time = (1 - (torrent["progress"] / 100)) * \
                      (torrent["size"] / torrent["download_rate"])
        return approx_time

    def delete_folder(self, folder_id):
        """ Delete folder with given id """
        form_data = {
            "delete_arr": "[{{\"type\": \"folder\", \"id\": \"{folder_id}\"}}]"
        }
        form_data["delete_arr"] = form_data["delete_arr"].\
                                    format(folder_id = folder_id)
        resp = self._make_request(Seedr._BASE_URL + Seedr._DELETE, form_data)
        return (result in resp and result is True)

