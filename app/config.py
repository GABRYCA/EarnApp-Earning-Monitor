import os
import io
import json
import pymysql
from time import sleep


class Configuration:
    def __init__(self) -> None:
        self.check_for_existing_config()
        # Delay before checking env. Solves docker issues.
        sleep(2)
        # if config doesn't exist
        if self.config_file_exists:
            self.__want_to_reset_config()
            if self.__reuse_config == True:
                self.load_config()
            else:
                self.ask_config()
        else:
            self.ask_config()

        self.fix_bugs()

    def fix_bugs(self):
        self.__fix_delay_bug()

    def ask_config(self):
        self.AUTH = (input("Enter the oauth-refresh-token from EarnApp dashboard\n\t: ")
                     if os.environ.get("AUTH") is None else os.environ.get("AUTH"))
        # 10 Minutes recommended by Vita
        self.DELAY = (10 if os.environ.get("DELAY")
                      is None else int(os.environ.get("DELAY")))
        self.WEBHOOK_URL = (input("Enter the Discord WebHook URL\n\t: ") if os.environ.get(
            "WEBHOOK_URL") is None else os.environ.get("WEBHOOK_URL"))
        self.AUTOMATIC_REDEEM = (input("Do you want to use automatic redeeming?\n\t[i] This helps getting your "
                                             "money faster.\n\t[i] If you don't want to use this feature just put 0 here else put the belance that has to be exceeted here [>2.5]\n\t: ")) if os.environ.get("AUTOMATIC_REDEEM") is None \
            else os.environ.get("AUTOMATIC_REDEEM")
        if input("Do you want to use a Mysql/MariaDB database?\n\tYes/No: ").lower() == "yes":
            endloop = False
            while not endloop:
                self.DB_HOST = input("Enter the host of the database (example: 'localhost')\n\t: ")
                self.DB_USER = input("Enter the username of the database (example: 'root')\n\t: ")
                self.DB_PASSWORD = input("Enter the password of the database (example: '')\n\t: ")
                self.DB_NAME = "earnapp_" + input("Enter the name of the database (example: 'monitor')\n\t: ")
                endloop = True
                # Test connection
                try:
                    cnx = pymysql.connect(user=self.DB_USER, password=self.DB_PASSWORD, host=self.DB_HOST)
                    cnx.close()
                except Exception as e:
                    print("Couldn't connect to the database.\n\tError: " + str(e))
                    self.DB_HOST = None
                    self.DB_USER = None
                    self.DB_PASSWORD = None
                    self.DB_NAME = None
                    if input("Do you want to try again?\n\tYes/No: ").lower() == "yes":
                        endloop = False
                    else:
                        endloop = True


        if self.DB_HOST is not None:
            cnx = pymysql.connect(user=self.DB_USER, password=self.DB_PASSWORD, host=self.DB_HOST)
            cursor = cnx.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS " + self.DB_NAME)
            cursor.execute("USE " + self.DB_NAME)
            cursor.execute("CREATE TABLE IF NOT EXISTS earnings (time datetime, traffic double, earnings double)")
            cnx.commit()
            print("Database and table created.")
            cnx.close()

        self.create_config()

    def __want_to_reset_config(self):
        if os.environ.get('container', False) == 'docker':
            self.__reuse_config = True
            return
        got_response = False
        while(not got_response):
            response = input("Want to use existing configuration? (yes/no): ")
            if response.lower() == "yes":
                got_response = True
                self.__reuse_config = True
            elif response.lower() == "no":
                got_response = True
                self.__reuse_config = False
            else:
                print("Didn't quite understand, try again!")

    def check_for_existing_config(self):
        self.home_directory = os.path.expanduser("~")
        self.program_data_folder = ".earnapp-earning-monitor"
        self.config_file_name = "config.json"

        self.program_directory = os.path.join(self.home_directory, self.program_data_folder)
        self.config_file_path = os.path.join(self.program_directory, self.config_file_name)

        self.config_file_exists = os.path.exists(self.config_file_path)

    def create_config(self):
        if os.environ.get('container', False) == 'docker':
            print("Detected container runtime.")
        else:
            # If config file doesn't exist
            if not self.config_file_exists:
                # If direcotry doesn't exist, create dir
                if not os.path.exists(self.program_directory):
                    os.mkdir(self.program_directory)
            config = {
                "AUTH": self.AUTH,
                "DELAY": self.DELAY,
                "WEBHOOK_URL": self.WEBHOOK_URL,
                "AUTOMATIC_REDEEM": self.AUTOMATIC_REDEEM,
                "DB_HOST": self.DB_HOST,
                "DB_USER": self.DB_USER,
                "DB_PASSWORD": self.DB_PASSWORD,
                "DB_NAME": self.DB_NAME
            }
            with io.open(self.config_file_path, "w", encoding="utf-8") as stream:
                json.dump(config, stream, indent=2)

    def load_config(self):
        with io.open(self.config_file_path, "r", encoding="utf-8") as stream:
            try:
                config_data = json.load(stream)
                self.AUTH = config_data["AUTH"]
                self.DELAY = config_data["DELAY"]
                self.WEBHOOK_URL = config_data["WEBHOOK_URL"]
                self.AUTOMATIC_REDEEM = config_data["AUTOMATIC_REDEEM"]
            except:
                print("Looks like your config file is missing paramters... Please reconfigure.")
                exit(1)

    def __fix_delay_bug(self):
        if self.DELAY < 0 or self.DELAY >= 60:
            print('Found invalid delay configuration. Fixing..!')
            self.DELAY = 10 # Standart
            self.create_config()

if __name__ == "__main__":
    config = Configuration()
